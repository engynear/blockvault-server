from typing import List
from pydantic import BaseModel
from db.models import Model

class ModelIn(BaseModel):
    name: str
    type: str
    description: str = None
    preview_image_path: str = None
    bbmodel_file_path: str = None
    json_file_path: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True

class ModelOut(BaseModel):
    id: int
    name: str
    type: str
    description: str = None
    preview_image_path: str = None
    bbmodel_file_path: str = None
    json_file_path: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True

class ResourcepackModelItem(BaseModel):
    model_id: int
    change_type: str
    change_item: str = None
    custom_model_data: int = None

class ResourcePackSoundItem(BaseModel):
    sound_id: int

class ResourcepackIn(BaseModel):
    name: str
    version: str
    description: str = None
    models: List[ResourcepackModelItem] = []
    sounds: List[ResourcePackSoundItem] = []

    class Config:
        orm_mode = True

class ResourcepackOut(BaseModel):
    id: int
    name: str
    version: str
    description: str = None
    resourcepack_file_path: str = None
    models_id: int = None
    sounds_id: int = None

    class Config:
        orm_mode = True