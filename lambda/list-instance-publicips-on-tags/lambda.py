import boto3
import csv
import io

client = boto3.client('autoscaling')
clientips=boto3.client('ec2')
s3 = boto3.client('s3')

paginator = client.get_paginator('describe_auto_scaling_groups')

ipdict = {} 
iplist = []

page_iterator = paginator.paginate(
   PaginationConfig = {
      'PageSize': 100
   }
)

def lambda_handler(event, context):
   csvio= io.StringIO()
   writer = csv.writer(csvio)
   writer.writerow([
      'IPAddress'
   ])


   filtered_asgs = page_iterator.search(
      'AutoScalingGroups[] | [?contains(Tags[?Key==`{}`].Value, `{}`)]'.format('type', 'node')
   )

   for asg in filtered_asgs:
      response = client.describe_auto_scaling_groups(
             AutoScalingGroupNames=[
        asg['AutoScalingGroupName'],
      ],
      )
      instances=response["AutoScalingGroups"][0]["Instances"]
      instanceids=[]
      for i in instances:
         instanceids.append(i["InstanceId"])
         #print (i["InstanceId"])
         instaneips=[]
         instanceips=clientips.describe_addresses(
            Filters = [
               {
                  'Name' : 'instance-id',
                  'Values' : [i['InstanceId']],
               },
            ],
         )
         reservations = clientips.describe_instances(InstanceIds=[i['InstanceId']]).get("Reservations")
         for reservation in reservations:
            for instance in reservation['Instances']:
               publicip = instance.get("PublicIpAddress")
               encoded_string = publicip.encode("utf-8")
               iplist.append(instance.get("PublicIpAddress"))

   
   for elem in iplist:
      print(elem)
      writer.writerow([elem])

   s3.put_object(Body=csvio.getvalue(), ContentType='application/vnd.ms-excel', Bucket='eyewatech-asg-node-bucket', Key='node') 
   csvio.close()


   

