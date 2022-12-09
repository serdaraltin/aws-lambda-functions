"""
Enviroments >>

DB_RESOURCE	dynamodb
INSTANCE_TYPE	g4dn.xlarge
KEY_NAME	Base
REGION	eu-north-1
SECURITY_GROUP_ID	sg-04707065899d32695
TABLE_NAME	Image
"""


import json
import os
import boto3
import datetime

INSTANCE_TYPE = os.environ['INSTANCE_TYPE']
KEY_NAME = os.environ['KEY_NAME']
SECURITY_GROUP_ID = os.environ['SECURITY_GROUP_ID']

REGION = os.environ["REGION"]
DB_RESOURCE = os.environ['DB_RESOURCE']
TABLE_NAME = os.environ["TABLE_NAME"]

EC2_RESOURCE = boto3.resource('ec2', region_name=REGION)
DB_CLIENT  = boto3.resource(DB_RESOURCE)
TABLE = DB_CLIENT.Table(TABLE_NAME)

DATE = str(datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))


def get_last_ami():
    response = TABLE.scan()
    data = response['Items']
    last_index = len(data)-1
    return data[last_index]['ami_id']

def create_instance(ami_id):
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': 'AutoCreate('+ami_id+'/'+ DATE +')'
                },
            ]
        },
    ]
    
    instance = EC2_RESOURCE.create_instances(
        ImageId=ami_id,
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        MaxCount=1,
        MinCount=1,
        TagSpecifications=TagSpecifications,
        SecurityGroupIds=[SECURITY_GROUP_ID]
    )
    return instance[0]
    
def lambda_handler(event, context):

    create_instance(get_last_ami())
    return {
        'statusCode': 200,
        'body': 'pass'
    }
 
