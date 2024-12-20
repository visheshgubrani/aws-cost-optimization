import boto3
from typing import Any 
import logging 

logger = logging.get(__name__)

def get_aws_client(service_name: str) -> Any:
  """
  Get an AWS client for the specified service with error handling.
    
    Args:
        service_name (str): Name of the AWS service (e.g., 'ec2', 'sns')
        
    Returns:
        boto3.client: AWS service client
  """
  try:
    return boto3.client(service_name)
  except Exception as e:
    logger.error(f"Failed to create AWS client for {service_name}")
    raise