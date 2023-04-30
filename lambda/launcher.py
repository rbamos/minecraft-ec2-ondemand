import boto3

REGION = 'us-east-1'
INSTANCE_ID = ''


def lambda_handler(event, context):
    """Updates the desired count for a service."""

    ec2 = boto3.client('ec2', region_name=REGION)
    response = ec2.describe_instances(
        InstanceIds=[INSTANCE_ID]
    )

    state = response["Reservations"][0]["Instances"][0]["State"]["Name"]

    if state in ["stopped", "stopping", "shutting-down"]:
        ec2.start_instances(
            InstanceIds=[INSTANCE_ID]
        )
        print(f"Started instance {INSTANCE_ID}")
    else:
        print(f"{INSTANCE_ID} already {state}")