import os.path
import json
import urllib.parse
import boto3
import email
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

print('Loading function')

s3 = boto3.client('s3')

def send_email(sender, recipient, aws_region, subject, file_name):
    BODY_TEXT = "Hello,\r\nPlease find the attached file."
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>Please find the attached file.</p>
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
        print("File exists")
    else:
        print("File does not exists")
    msg.attach(msg_body)
    msg.attach(att)
    try:
        response = client.send_raw_email(
            Source=msg['From'],
            Destinations=[
                msg['To']
            ],
            RawMessage={
                'Data':msg.as_string(),
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:", response['MessageId'])

def lambda_handler(event, context):
    BUCKET = event['Records'][0]['s3']['bucket']['name']
    KEY = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    try:
        response = s3.get_object(Bucket=BUCKET, Key=KEY)
        print("CONTENT TYPE: " + response['ContentType'])
        FILE_NAME = os.path.basename(KEY)
        TMP_FILE_NAME = '/tmp/' +FILE_NAME
        s3.download_file(BUCKET, KEY, TMP_FILE_NAME)
        ATTACHMENT = TMP_FILE_NAME
        print(ATTACHMENT)
        send_email('email@gmail.com', 'email@gmail.com', 'eu-central-1', 'AWS LAMBDA TEST', ATTACHMENT)
        return response['ContentType']
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(KEY, BUCKET))
        raise e