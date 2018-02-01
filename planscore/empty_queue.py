import boto3, io, csv, json
from datetime import datetime
from . import constants

def main():
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    sqs = boto3.client('sqs', endpoint_url=constants.SQS_ENDPOINT_URL)

    wrote_something = False
    buffer = io.StringIO()
    fields = ('upload', 'prefix', 'tile', 'size', 'time')
    out = csv.DictWriter(buffer, fields, dialect='excel-tab')
    out.writeheader()
    
    while True:
        resp = sqs.receive_message(QueueUrl=constants.SQS_QUEUEURL,
            MaxNumberOfMessages=10)
        
        if 'Messages' not in resp:
            break
        
        for message in resp['Messages']:
            try:
                row = json.loads(message['Body'])
                out.writerow({k: row.get(k) for k in out.fieldnames})
            except:
                print('Fail', message['ReceiptHandle'])
            else:
                wrote_something = True
                print('OK', message['ReceiptHandle'])
            finally:
                sqs.delete_message(QueueUrl=constants.SQS_QUEUEURL,
                    ReceiptHandle=message['ReceiptHandle'])
    
    if not wrote_something:
        return
    
    print(buffer.getvalue())

    key = 'logs/{}.txt'.format(datetime.now().strftime('%Y%m%dT%H%M%S'))
    body = buffer.getvalue().encode('utf8')
    s3.put_object(Bucket=constants.S3_BUCKET, Key=key, Body=body, ContentType='text/plain')

def lambda_handler(event, context):
    '''
    '''
    return main()
