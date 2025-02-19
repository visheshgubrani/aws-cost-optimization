# AWS EBS Snapshot Manager

A Lambda function to manage Amazon EBS snapshots, reducing storage costs while maintaining safeguards against accidental deletion of important data.

## Features

- **Cost Optimization**: Automatically deletes old snapshots based on configurable retention periods
- **Safety First**: Multiple protection mechanisms to prevent deletion of critical snapshots
- **Flexible Configuration**: Customize retention policies through environment variables
- **Comprehensive Logging**: Detailed logging of all operations for auditability
- **Dry Run Mode**: Test configuration without actually deleting any snapshots

## Protection Mechanisms

1. **Minimum Snapshot Retention**: Always keeps a minimum number of snapshots per volume
2. **Tagged Protection**: Snapshots with a protection tag are never deleted
3. **Critical Volume Protection**: All snapshots from critical volumes are preserved
4. **In-use Snapshot Protection**: Snapshots currently in use (e.g., by AMIs) are skipped

## Requirements

- AWS account with permissions to manage EBS snapshots
- Basic understanding of AWS Lambda and IAM roles

## Deployment Guide

### 1. Create IAM Role

Create an IAM role for your Lambda function with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSnapshots",
        "ec2:DescribeVolumes",
        "ec2:DeleteSnapshot"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 2. Create Lambda Function

1. Navigate to the AWS Lambda console
2. Click "Create function"
3. Select "Author from scratch"
4. Configure basic settings:
   - Name: `ebs-snapshot-manager`
   - Runtime: Python 3.9 (or newer)
   - Architecture: x86_64
   - Permissions: Use the IAM role created in step 1
5. Click "Create function"
6. Copy the Python code from this repository into the code editor
7. Configure environment variables (see Configuration section below)
8. Set timeout to 5 minutes (300 seconds)
9. Click "Deploy"

### 3. Schedule the Lambda Function

1. Go to the "Configuration" tab in your Lambda function
2. Click on "Triggers" in the left sidebar
3. Click "Add trigger"
4. Select "EventBridge (CloudWatch Events)"
5. Create a new rule:
   - Rule name: `daily-snapshot-cleanup`
   - Rule type: Schedule expression
   - Schedule expression: `cron(0 3 * * ? *)` (runs daily at 3:00 AM UTC)
6. Click "Add"

## Configuration

Configure the function using the following environment variables:

| Variable                    | Description                              | Default         |
| --------------------------- | ---------------------------------------- | --------------- |
| `RETENTION_DAYS`            | Number of days to keep snapshots         | 30              |
| `MIN_SNAPSHOTS_TO_KEEP`     | Minimum snapshots to retain per volume   | 3               |
| `DRY_RUN`                   | Run in simulation mode without deletions | True            |
| `PROTECTED_TAG_KEY`         | Tag key used to mark protected snapshots | ProtectSnapshot |
| `PROTECTED_TAG_VALUE`       | Tag value for protected snapshots        | true            |
| `CRITICAL_VOLUME_TAG_KEY`   | Tag key for critical volumes             | CriticalVolume  |
| `CRITICAL_VOLUME_TAG_VALUE` | Tag value for critical volumes           | true            |

## Tagging Your Resources

### Protecting Specific Snapshots

Add the following tag to any snapshot you want to protect:

```
Key: ProtectSnapshot
Value: true
```

### Protecting All Snapshots from Critical Volumes

Add the following tag to any volume whose snapshots should never be deleted:

```
Key: CriticalVolume
Value: true
```

## Getting Started

1. Deploy the Lambda function using the steps above
2. First run with `DRY_RUN` set to `True` to validate behavior
3. Review CloudWatch logs to see which snapshots would be deleted
4. Once satisfied, set `DRY_RUN` to `False` to enable actual deletion

## CloudWatch Logs

The function logs detailed information about its operations. To view logs:

1. Go to the AWS CloudWatch console
2. Navigate to "Log groups"
3. Find the log group named `/aws/lambda/ebs-snapshot-manager`
4. Click on the latest log stream to view execution details

## Best Practices

1. **Start Conservatively**: Begin with longer retention periods and more minimum snapshots
2. **Tag Critical Resources**: Proactively tag important volumes and snapshots
3. **Monitor Regularly**: Check logs after each execution
4. **Audit Periodically**: Review protected resources quarterly

## Troubleshooting

### Common Issues

**No snapshots are being deleted**

- Check if `DRY_RUN` is set to `True`
- Verify retention period isn't too long
- Look for tag-based protections that might be preventing deletion

**Lambda timing out**

- Increase the Lambda timeout setting
- Consider adding pagination if you have thousands of snapshots

**Permission errors**

- Verify IAM role has proper permissions
- Check for resource-based policies restricting access

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
