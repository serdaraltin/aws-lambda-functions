"""
Enviroments >>

DB_RESOURCE	dynamodb
INSTANCE	i-07a5be2b5180a2ba6
REGION	eu-north-1
TABLE_NAME	Image
"""

import json
import os
import boto3
import datetime
import dateutil.tz
import time

INSTANCEID = os.environ["INSTANCE"]
REGION = os.environ["REGION"]
TABLE_NAME = os.environ["TABLE_NAME"]

EC2_CLIENT = boto3.client('ec2', region_name=REGION)
DB_CLIENT = boto3.resource(os.environ['DB_RESOURCE'])


def get_datetime():
    istanbul = dateutil.tz.gettz('Asia/Istanbul')
    current_date = datetime.datetime.now(tz=istanbul)
    return str(current_date.strftime("%Y-%m-%dT%H-%M-%S"))

def get_image_list():
    return EC2_CLIENT.describe_images(Owners=['self'])['Images']

def check_image(ami_id):
    for item in get_image_list():
        if item['ImageId'] == ami_id:
            return True
    return False

def check_record(ami_id):
    TABLE_IMAGE = DB_CLIENT.Table(TABLE_NAME)
    response = TABLE_IMAGE.scan()
    images = response['Items']
    
    for image in images:
        
        if ami_id == image['ami_id']:
            print(image['ami_id'], ami_id)
            return True
    return False
    
def delete_snapshot(ami_id):
    my_id = boto3.client('sts').get_caller_identity()['Account']
    snapshots = EC2_CLIENT.describe_snapshots(MaxResults=1000, OwnerIds=[my_id])['Snapshots']
    for snapshot in snapshots:
        if ami_id in snapshot['Description']:
            return EC2_CLIENT.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
            
    return None
    
    
def delete_image(ami_id):
    if check_image(ami_id):       
        deleted_image = EC2_CLIENT.deregister_image(DryRun=False, ImageId=ami_id)
        return (deleted_image, delete_snapshot(ami_id))


def clean_old_image(deep=2):
    def get_creation_date(element):
        return element['CreationDate']
        
    images = get_image_list()
    images.sort(key=get_creation_date)
    
    for i in range(0,len(images)-deep):
        if check_record(images[i]['ImageId']):
            delete_image(images[i]['ImageId'])

def add_image(ami_id, instance_id=INSTANCEID, table_name=TABLE_NAME, db_client=DB_CLIENT):
    table = DB_CLIENT.Table(TABLE_NAME)
    
    ami={
        'ami_id': ami_id,
        'instance_id': instance_id,
        'creation_date': get_datetime()
    }    
    
    table.put_item(Item=ami)
    return ami

def lambda_handler(event, context):
    if False:
        #Test Scope
        return clean_old_image()
        
    name = "AutoCreate("+ get_datetime() +")"
    description = "AMI for "+ INSTANCEID +" created with lambda (by Serdar)"
   
    new_image = EC2_CLIENT.create_image(InstanceId=INSTANCEID, Name=name, Description=description, NoReboot=True)
    time.sleep(1)
    
    if check_image(new_image['ImageId']):
        record = add_image(new_image['ImageId'])
        clean_old_image()
        return {
            'statusCode': 200,
            'body': record
        }
    else:
        return {
            'statusCode': 417,
            'body': json.dumps('Cannot create new image !')
        }
