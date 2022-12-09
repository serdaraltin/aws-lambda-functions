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

INSTANCEID = os.environ["INSTANCE"]
REGION = os.environ["REGION"]
TABLE_NAME = os.environ["TABLE_NAME"]

EC2_CLIENT = boto3.client('ec2', region_name=REGION)
DB_CLIENT = boto3.resource(os.environ['DB_RESOURCE'])

DATE = str(datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))

def add_image(ami_image, instance_id=INSTANCEID, table_name=TABLE_NAME, db_client=DB_CLIENT):
    table = DB_CLIENT.Table(TABLE_NAME)
    
    ami_id = ami_image['ImageId']
    creation_date = ami_image['CreationDate']
    
    table.put_item(
        Item={
                'ami_id': ami_id,
                'instance_id': instance_id,
                'creation_date': creation_date
        }    
    )
    
def lambda_handler(event, context):
    name = "AutoCreate("+INSTANCEID+"/"+ DATE +")"
    description = "AMI for "+ INSTANCEID +" created by lambda (from serdar)"
   
    ami_image = EC2_CLIENT.create_image(InstanceId=INSTANCEID,  
    Name=name, NoReboot=True)
    
    image_list = EC2_CLIENT.describe_images(Owners=['self'])
    for ami_item in image_list['Images']:
        if ami_item['ImageId'] == ami_image['ImageId']:
            add_image(ami_item)
            return {
                'statusCode': 200,
                'body': json.dumps('Created new ami from Instance('+ INSTANCEID+")")
            }
            
            
    return {
            'statusCode': 417,
            'body': json.dumps('Failed !')
    }
    
    
