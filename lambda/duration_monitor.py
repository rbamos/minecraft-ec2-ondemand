import boto3
import datetime

MAX_TIME = datetime.timedelta(hours=8)
INSTANCE_ID = ''
TOPIC_ARN = ''

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')
    
    instance = ec2.describe_instances(InstanceIds=[INSTANCE_ID])['Reservations'][0]['Instances'][0]
    
    if instance['State']['Name'] == 'stopped':
        return {'message': f"Instance {INSTANCE_ID} is stopped."}

    # This turns out to be how long since it started running, not since the instance was launched
    launch_time = instance['LaunchTime']
    now = datetime.datetime.now(launch_time.tzinfo)
    running_time = now - launch_time

    if running_time > MAX_TIME:
        message = f"Instance {INSTANCE_ID} has been running for {running_time} > {MAX_TIME}."
        response = sns.publish(TopicArn=TOPIC_ARN, Message=message)
        return {'message': message}
    
    return {'message': f"Instance  {INSTANCE_ID} runtime: {running_time} < {MAX_TIME}."}