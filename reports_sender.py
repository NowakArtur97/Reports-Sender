import os.path
import json
import urllib.parse
import boto3
import email
import cfnresponse
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

print('Loading function')

SENDER = os.environ['SENDER']
EMAIL_SUBJECT = os.environ['EMAIL_SUBJECT']
RECIPIENTS = os.environ['RECIPIENTS'].split(",")
REGION = os.environ['REGION']
BUCKET = os.environ['BUCKET_NAME']

s3 = boto3.client('s3')

def clear_bucket():
    s3.Bucket(BUCKET).objects.all().delete()
    print("Successfully cleared bucket: " + BUCKET)

def download_report(event):
    KEY = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    fileName = os.path.basename(KEY)
    tmpFileName = '/tmp/' +fileName
    s3.download_file(BUCKET, KEY, tmpFileName)
    print("Successfully downloaded the report from bucket: " + BUCKET)
    return tmpFileName

def send_report(sender, recipient, aws_region, subject, file_name):
    BODY_TEXT = "Hello,\r\nPlease find the attached report."
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello</h1>
    <p>Please find the attached report.</p>
    </body>
    </html>
    """
    CHARSET = "utf-8"
    client = boto3.client('ses',region_name=aws_region)
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject 
    msg['From'] = sender 
    msg['To'] = recipient
    msg_body = MIMEMultipart('alternative')
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    att = MIMEApplication(open(file_name, 'rb').read())
    att.add_header('Content-Disposition','attachment', filename="report.csv")
    if os.path.exists(file_name):
        print("File: " + file_name + " exists")
        msg.attach(msg_body)
        msg.attach(att)
        client.send_raw_email(
                Source=msg['From'],
                Destinations=[
                    msg['To']
                ],
                RawMessage={
                    'Data':msg.as_string(),
                }
            )
        print('Reports sent successfully')
    else:
        message = "File: " + file_name + " does not exist"
        print(message)
        raise Exception(message)

def lambda_handler(event, context):
    responseData = {}
    attachment = {}
    if 'RequestType' in event:
        try:
            if event['RequestType'] == 'Delete':
                clear_bucket()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
        except Exception as e:
            print('Exception when setting up the infrastructure')
            print(e)
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    try:
        attachment = download_report(event)
    except Exception as e:
        print('Exception when fetching report from bucket')
        print(e)
    try:
        for recipient in RECIPIENTS:
            send_report(SENDER, recipient, REGION, EMAIL_SUBJECT, attachment)
    except Exception as e:
        print('Exception when sending reports')
        print(e)