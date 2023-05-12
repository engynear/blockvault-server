import os
os.environ['DATABASE_URL'] = "postgresql://engynear:132wersdf@localhost:5432/blockvault"
os.environ['AWS_ACCESS_KEY_ID'] = "minio"
os.environ['AWS_SECRET_ACCESS_KEY'] = "miniosecret"
os.environ['S3_URL'] = "http://localhost:9000"

from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_URL: str

settings = Settings(_env_file=".env", _env_file_encoding="utf-8")