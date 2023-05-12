from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

def create_s3_buckets():
    import boto3
    from botocore.utils import fix_s3_host
    from core.config import settings

    s3 = boto3.resource(service_name='s3', endpoint_url=settings.S3_URL)
    s3.meta.client.meta.events.unregister('before-sign.s3', fix_s3_host)
    client = s3.meta.client

    #check if bucket exists
    if not client.list_buckets()['Buckets']:
        client.create_bucket(Bucket='model-previews')
        client.create_bucket(Bucket='model-files')
