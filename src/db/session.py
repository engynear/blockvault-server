from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from botocore.utils import fix_s3_host
import boto3

from core.config import settings

# Создаем engine
engine = create_engine(settings.DATABASE_URL)

# Создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция зависимости для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_s3_client():
    s3 = boto3.resource(service_name='s3', endpoint_url=settings.S3_URL)
    s3.meta.client.meta.events.unregister('before-sign.s3', fix_s3_host)
    client = s3.meta.client
    
    try:
        yield client
    finally:
        client.close()