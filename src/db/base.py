from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

def create_s3_buckets(remove_existing=False):
    import boto3
    from botocore.utils import fix_s3_host
    from core.config import settings

    s3 = boto3.resource(service_name='s3', endpoint_url=settings.S3_URL)
    s3.meta.client.meta.events.unregister('before-sign.s3', fix_s3_host)
    client = s3.meta.client

    if remove_existing:
        for bucket in client.list_buckets()['Buckets']:
            for obj in client.list_objects(Bucket=bucket['Name'])['Contents']:
                client.delete_object(Bucket=bucket['Name'], Key=obj['Key'])
            client.delete_bucket(Bucket=bucket['Name'])

    #check if bucket exists
    if not client.list_buckets()['Buckets']:
        client.create_bucket(Bucket='blockvault-bucket')
