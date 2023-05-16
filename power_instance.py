import json
import boto3
import os

REGION = os.environ["REGION"]
ec2 = boto3.client("ec2", region_name=REGION)

def get_state(instance_id):
    #Running Code: 16
    #Stopping Code: 64
    #Stopped Code: 80
    #Pending Code: 0
    try:
        instances = ec2.describe_instances(InstanceIds=[instance_id])
        return instances['Reservations'][0]['Instances'][0]['State']
    except Exception:
        return None


def start_instance(instance_id):
    state_code = get_state(instance_id)['Code']

    if state_code == 0 or state_code == 16:
        #pending or running
        return False
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        return True
    except Exception:
        return False

    
def stop_instance(instance_id):
    state_code = get_state(instance_id)['Code']

    if state_code == 80 or state_code == 64:
        #stopping or stopped    
        return False
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        return True
    except Exception:
        return False

def return_data(status_code, operation, instance_id):
     
    data={
        'operation': operation,
        'instanceId': instance_id,
        'state': get_state(instance_id)
    }
    
    return {
        "isBase64Encoded": False,
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(data)
    }
    
def operation_instance(operation, instance_id):

    if not get_state(instance_id):
        return return_data(400, False, None)

    if operation == 'start':
        return return_data(200, start_instance(instance_id), instance_id)
    elif operation == 'stop':
        return return_data(200, stop_instance(instance_id), instance_id)
    elif operation == 'state':
        return return_data(200, None, instance_id)


def lambda_handler(event, context):

    try:
        operation = event['queryStringParameters']['operation']
        instance_id = event['queryStringParameters']['instanceId']
        
        return operation_instance(operation, instance_id)
    except Exception:
        return return_data(400, False, None)
 
