from typing import List
from pydantic import BaseModel
from db.models import Model

class ResourcepackModelItem(BaseModel):
    model_id: int
    change_type: str
    change_item: str = None
    custom_model_data: int = None

class ResourcePackSoundItem(BaseModel):
    sound_id: int
    sound_name: str

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
    models: List[ResourcepackModelItem] = []
    sounds: List[ResourcePackSoundItem] = []

    class Config:
        orm_mode = True
