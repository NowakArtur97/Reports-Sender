import os.path
import boto3
import cfnresponse

print('Loading function')

BUCKET = os.environ['BUCKET_NAME']

s3 = boto3.resource('s3')

def clear_bucket():
    s3.Bucket(BUCKET).objects.all().delete()
    print("Successfully cleared bucket: " + BUCKET)

def lambda_handler(event, context):
    responseData = {}
    if event['RequestType'] == 'Delete':
        try:
            clear_bucket()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            print('Exception when cleaning bucket: ' + BUCKET)
            print(e)
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    else:
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)