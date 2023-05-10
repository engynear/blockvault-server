from typing import List
from pydantic import BaseModel
from db.models import Model

class ModelIn(BaseModel):
    name: str
    type: str
    description: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True

class ModelOut(BaseModel):
    id: int
    name: str
    type: str
    description: str = None
    tags: List[str] = []

    class Config:
        orm_mode = True