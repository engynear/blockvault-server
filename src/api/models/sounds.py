from typing import List
from pydantic import BaseModel
from db.models import Model

class SoundIn(BaseModel):
    name: str
    description: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True

class SoundOut(BaseModel):
    id: int
    name: str
    description: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True