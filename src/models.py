from typing import List
from pydantic import BaseModel
from fastapi import UploadFile

class Model(BaseModel):
    id: int
    name: str
    preview_path: str = None
    type: str
    tags: List[str] = []

class ModelPayload(BaseModel):
    modelName: str = ""
    modelType: str = ""
    modelTags: List[str]
    modelFile: bytes
    previewImage: bytes