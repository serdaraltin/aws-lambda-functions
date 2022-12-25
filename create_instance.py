import json
import os
import boto3
import datetime
import dateutil.tz

INSTANCE_TYPE = os.environ['INSTANCE_TYPE']
KEY_NAME = os.environ['KEY_NAME']
SECURITY_GROUP_ID = os.environ['SECURITY_GROUP_ID']
HOSTED_ZONE_ID = os.environ['HOSTED_ZONE_ID']
HOSTED_ZONE_DOMAIN = os.environ['HOSTED_ZONE_DOMAIN']

REGION = os.environ["REGION"]
DB_RESOURCE = os.environ['DB_RESOURCE']
TABLE_NAME = os.environ["TABLE_NAME"]

EC2_RESOURCE = boto3.resource('ec2', region_name=REGION)
EC2_CLIENT = boto3.client('ec2', region_name=REGION)
DB_CLIENT  = boto3.resource(DB_RESOURCE)
TABLE = DB_CLIENT.Table(TABLE_NAME)
TABLE_NAME_IMAGE = "Image"

istanbul = dateutil.tz.gettz('Asia/Istanbul')
current_date = datetime.datetime.now(tz=istanbul)
DATE = str(current_date.strftime("%Y-%m-%dT%H-%M-%S"))

ROUTE53_CLIENT = boto3.client("route53", region_name=REGION)

def get_last_ami():
    def get_creation_date(element):
        return element['creation_date']
        
    TABLE_IMAGE = DB_CLIENT.Table(TABLE_NAME_IMAGE)
    response = TABLE_IMAGE.scan()
    data = response['Items']
    
    data.sort(key=get_creation_date)
    
    return data[-1]['ami_id']

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
    
    instance={
        'instance_id': instance_id ,
        'public_ip': public_ip,
        'begin_map': begin_map,
        'creation_date': DATE
    }  
    table.put_item(Item=instance)  
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': instance
    }
    
def update_subdomain_a_record(public_ip):
    aName = public_ip.replace(".", "-")
    aName = aName + HOSTED_ZONE_DOMAIN
    
    ROUTE53_CLIENT.change_resource_record_sets(
        HostedZoneId=HOSTED_ZONE_ID,
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": aName,
                        "Type": "A",
                        "ResourceRecords": [
                            {
                                "Value": public_ip
                            }
                        ],
                        "TTL": 300,
                    },
                }
            ]
        },
    )

def lambda_handler(event, context):
    instance = create_instance(get_last_ami())
    instance_id = instance.instance_id
    public_ip = get_ip(instance_id)
    begin_map = 'default'
    try:        
        begin_map = event['begin_map']
    except :    
        pass

    retvalue = add_instance(instance_id, public_ip, begin_map)
    update_subdomain_a_record(public_ip)
    
    return retvalue


 
