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

istanbul = dateutil.tz.gettz('Asia/Istanbul')
current_date = datetime.datetime.now(tz=istanbul)
DATE = str(current_date.strftime("%Y-%m-%dT%H-%M-%S"))

def add_image(ami_image, instance_id=INSTANCEID, table_name=TABLE_NAME, db_client=DB_CLIENT):
    table = DB_CLIENT.Table(TABLE_NAME)
    
    ami={
        'ami_id': ami_image['ImageId'],
        'instance_id': instance_id,
        'creation_date': DATE
    }    
    
    table.put_item(Item=ami)
    return {
        'statusCode': 200,
        'body': ami
    }
    
def lambda_handler(event, context):
    name = "AutoCreate("+ DATE +")"
    description = "AMI for "+ INSTANCEID +" created with lambda (by Serdar)"
   
    ami_image = EC2_CLIENT.create_image(InstanceId=INSTANCEID, Name=name, Description=description, NoReboot=True)
        
    time.sleep(1)
    
    image_list = EC2_CLIENT.describe_images(Owners=['self'])

    for ami_item in image_list['Images']:
        if ami_item['ImageId'] == ami_image['ImageId']:
            return add_image(ami_item)
            
    return {
            'statusCode': 417,
            'body': json.dumps('Failed !')
    }
    
    
