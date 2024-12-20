# AWS EBS Snapshot Manager

A serverless solution for managing AWS EBS snapshots, implementing automated cleanup and cost optimization.

## Features

- Automated EBS snapshot cleanup based on retention policies
- AMI dependency checking to prevent deletion of in-use snapshots
- SNS notifications for operation reports
- Comprehensive logging and error handling
- Resource tagging for audit trails

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/snapshot-manager.git
cd snapshot-manager
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure AWS credentials:

- Set up AWS credentials using AWS CLI or environment variables
- Ensure proper IAM roles are configured for Lambda execution

4. Set up environment variables:

- `SNS_TOPIC_ARN`: ARN of the SNS topic for notifications
- `RETENTION_DAYS`: Number of days to retain snapshots (default: 30)

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## Deployment

1. Package the application:

```bash
zip -r function.zip src/ requirements.txt
```

2. Deploy to AWS Lambda:

- Create a new Lambda function
- Upload the function.zip package
- Configure environment variables
- Set the handler to `src.handlers.lambda_handler`
- Configure appropriate IAM roles and permissions

## IAM Permissions Required

The Lambda function requires the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeSnapshots",
        "ec2:DeleteSnapshot",
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:CreateTags",
        "ec2:DescribeImages",
        "sns:Publish"
      ],
      "Resource": "*"
    }
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
