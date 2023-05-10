from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import UploadFile, File
from typing import List

from sqlalchemy.orm import Session

from db.session import get_db, get_s3_client
from db.models import Resourcepack
from api.models.resourcepacks import ResourcepackIn, ResourcepackOut


router = APIRouter()

@router.get("/{resourcepack_id}", response_model=ResourcepackOut)
async def get_resourcepack(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")
    return resourcepack

@router.post("", response_model=ResourcepackOut)
async def create_resourcepack(resourcepack: ResourcepackIn, db: Session = Depends(get_db)):
    name = resourcepack.name
    version = resourcepack.version
    description = resourcepack.description
    models = resourcepack.models
    sounds = resourcepack.sounds

    db_resourcepack = Resourcepack(name=name, version=version, description=description)
    db.add(db_resourcepack)
    db.commit()
    db.refresh(db_resourcepack)
    return db_resourcepack
