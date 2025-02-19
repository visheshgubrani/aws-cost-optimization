import boto3
import logging
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables with defaults
RETENTION_DAYS = int(os.environ.get('RETENTION_DAYS', 30))
MIN_SNAPSHOTS_TO_KEEP = int(os.environ.get('MIN_SNAPSHOTS_TO_KEEP', 3))
DRY_RUN = os.environ.get('DRY_RUN', 'True').lower() == 'true'
PROTECTED_TAG_KEY = os.environ.get('PROTECTED_TAG_KEY', 'ProtectSnapshot')
PROTECTED_TAG_VALUE = os.environ.get('PROTECTED_TAG_VALUE', 'true')
CRITICAL_VOLUME_TAG_KEY = os.environ.get('CRITICAL_VOLUME_TAG_KEY', 'CriticalVolume')
CRITICAL_VOLUME_TAG_VALUE = os.environ.get('CRITICAL_VOLUME_TAG_VALUE', 'true')

def lambda_handler(event, context):
    """
    AWS Lambda function to manage EBS snapshots.
    Deletes snapshots older than RETENTION_DAYS while ensuring MIN_SNAPSHOTS_TO_KEEP
    are retained per volume and implementing safety checks.
    """
    logger.info(f"Starting EBS snapshot cleanup. Retention days: {RETENTION_DAYS}, "
                f"Min snapshots per volume: {MIN_SNAPSHOTS_TO_KEEP}, Dry run: {DRY_RUN}")
    
    ec2 = boto3.client('ec2')
    
    # Get all snapshots owned by this account
    try:
        snapshots = get_account_snapshots(ec2)
        logger.info(f"Found {len(snapshots)} snapshots in account")
    except ClientError as e:
        logger.error(f"Failed to retrieve snapshots: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error retrieving snapshots: {str(e)}"
        }
    
    # Group snapshots by volume
    volume_snapshots = group_by_volume(snapshots)
    
    deleted_count = 0
    protected_count = 0
    critical_volume_count = 0
    too_few_count = 0
    
    for volume_id, snaps in volume_snapshots.items():
        # Sort snapshots by creation date (oldest first)
        snaps.sort(key=lambda x: x['StartTime'])
        
        # Process each snapshot for the volume
        deleted, protected, critical, too_few = process_volume_snapshots(ec2, volume_id, snaps)
        
        deleted_count += deleted
        protected_count += protected
        critical_volume_count += critical
        too_few_count += too_few
    
    result = {
        'statusCode': 200,
        'body': {
            'dry_run': DRY_RUN,
            'deleted_snapshots': deleted_count,
            'protected_snapshots': protected_count,
            'critical_volume_snapshots': critical_volume_count,
            'too_few_snapshots': too_few_count,
            'retention_days': RETENTION_DAYS,
            'min_snapshots_per_volume': MIN_SNAPSHOTS_TO_KEEP
        }
    }
    
    logger.info(f"Snapshot cleanup completed: {result}")
    return result

def get_account_snapshots(ec2):
    """Retrieve all EBS snapshots owned by this account"""
    response = ec2.describe_snapshots(OwnerIds=['self'])
    return response['Snapshots']

def group_by_volume(snapshots):
    """Group snapshots by their source volume ID"""
    volume_snapshots = {}
    
    for snapshot in snapshots:
        volume_id = snapshot.get('VolumeId', 'unknown')
        if volume_id not in volume_snapshots:
            volume_snapshots[volume_id] = []
        volume_snapshots[volume_id].append(snapshot)
    
    return volume_snapshots

def process_volume_snapshots(ec2, volume_id, snapshots):
    """Process snapshots for a specific volume"""
    deleted = 0
    protected = 0
    critical = 0
    too_few = 0
    
    # Check if this is a critical volume
    if volume_id != 'unknown' and is_critical_volume(ec2, volume_id):
        logger.info(f"Volume {volume_id} is marked as critical. Extra protection applied.")
        critical = len(snapshots)
        return deleted, protected, critical, too_few
    
    # If we have too few snapshots, keep them all
    if len(snapshots) <= MIN_SNAPSHOTS_TO_KEEP:
        logger.info(f"Only {len(snapshots)} snapshots for volume {volume_id}, "
                   f"which is below minimum {MIN_SNAPSHOTS_TO_KEEP}. Keeping all.")
        too_few = len(snapshots)
        return deleted, protected, critical, too_few
    
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    
    # Keep track of how many we've deleted to ensure we keep MIN_SNAPSHOTS_TO_KEEP
    remaining = len(snapshots)
    
    # Process older snapshots first (they're sorted by date)
    for snapshot in snapshots:
        snapshot_id = snapshot['SnapshotId']
        start_time = snapshot['StartTime']
        
        # Always keep the minimum number of snapshots per volume
        if remaining <= MIN_SNAPSHOTS_TO_KEEP:
            logger.info(f"Keeping snapshot {snapshot_id} to maintain "
                       f"minimum {MIN_SNAPSHOTS_TO_KEEP} snapshots for volume {volume_id}")
            too_few += 1
            continue
        
        # Check if snapshot is protected by tag
        if is_protected_snapshot(snapshot):
            logger.info(f"Snapshot {snapshot_id} is protected by tag {PROTECTED_TAG_KEY}={PROTECTED_TAG_VALUE}")
            protected += 1
            remaining -= 1
            continue
        
        # Check if snapshot is old enough to delete
        if start_time < cutoff_date:
            try:
                if not DRY_RUN:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    logger.info(f"Deleted snapshot {snapshot_id} from {start_time}")
                else:
                    logger.info(f"Would delete snapshot {snapshot_id} from {start_time} (dry run)")
                deleted += 1
            except ClientError as e:
                if 'InvalidSnapshot.InUse' in str(e):
                    logger.warning(f"Snapshot {snapshot_id} is in use, cannot delete: {str(e)}")
                    protected += 1
                else:
                    logger.error(f"Error deleting snapshot {snapshot_id}: {str(e)}")
        else:
            logger.info(f"Snapshot {snapshot_id} is newer than {RETENTION_DAYS} days, keeping")
        
        remaining -= 1
    
    return deleted, protected, critical, too_few

def is_protected_snapshot(snapshot):
    """Check if a snapshot is protected by tags"""
    if 'Tags' not in snapshot:
        return False
    
    for tag in snapshot['Tags']:
        if tag['Key'] == PROTECTED_TAG_KEY and tag['Value'].lower() == PROTECTED_TAG_VALUE.lower():
            return True
    
    return False

def is_critical_volume(ec2, volume_id):
    """Check if volume is marked as critical"""
    try:
        response = ec2.describe_volumes(VolumeIds=[volume_id])
        
        if not response or 'Volumes' not in response or not response['Volumes']:
            # Volume might have been deleted, consider non-critical
            return False
        
        volume = response['Volumes'][0]
        
        if 'Tags' not in volume:
            return False
        
        for tag in volume['Tags']:
            if tag['Key'] == CRITICAL_VOLUME_TAG_KEY and tag['Value'].lower() == CRITICAL_VOLUME_TAG_VALUE.lower():
                return True
                
        return False
    except ClientError as e:
        if 'InvalidVolume.NotFound' in str(e):
            # Volume doesn't exist anymore, consider non-critical
            logger.info(f"Volume {volume_id} no longer exists")
            return False
        else:
            logger.error(f"Error checking volume {volume_id}: {str(e)}")
            # On error, assume it's critical to be safe
            return True