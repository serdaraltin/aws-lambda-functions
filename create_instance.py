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

TABLE_NAME_IMAGE = "Image"

DATE = str(datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))


def get_last_ami():
    TABLE_IMAGE = DB_CLIENT.Table(TABLE_NAME_IMAGE)
    response = TABLE_IMAGE.scan()
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
    
def get_ip(instance_id):
    ec2 = boto3.client('ec2')
    instances = ec2.describe_instances(InstanceIds=[instance_id])
    return instances['Reservations'][0]['Instances'][0]['PublicIpAddress']
  
  
def add_instance(instance_id, public_ip, begin_map):
    table = DB_CLIENT.Table(TABLE_NAME)
    
    table.put_item(
        Item={
            'instance_id': instance_id ,
            'public_ip': public_ip,
            'begin_map': begin_map
        }    
    )  

def lambda_handler(event, context):

    #instance = create_instance(get_last_ami())
    instance_id = 'i-07a5be2b5180a2ba6'#instance.instance_id
    public_ip = get_ip(instance_id)
    begin_map = event['begin_map']
    
        
    #add_instance(instance_id, public_ip, begin_map)
    

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': {
            'instance_id': instance_id,
            'public_ip': public_ip,
            'begin_map': begin_map
        }
    }
 
