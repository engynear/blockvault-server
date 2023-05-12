from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import UploadFile, File
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.session import get_db, get_s3_client
from db.models import Resourcepack, Model, Sound
from api.models.resourcepacks import ResourcepackIn, ResourcepackOut, ResourcepackModelItem, ResourcePackSoundItem
from api.models.sounds import SoundIn, SoundOut
import os
import shutil
import zipfile
import json

models_preview_placeholder = 'models-preview-placeholder.png'
RESOURCEPACKS_DIR = 'src/api/temp/'

router = APIRouter()

@router.get("", response_model=List[ResourcepackOut])
async def get_resourcepacks(db: Session = Depends(get_db)):
    resourcepacks = db.query(Resourcepack).all()
    return resourcepacks

@router.get("/{resourcepack_id}", response_model=ResourcepackOut)
async def get_resourcepack(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")
    return resourcepack

@router.get("/{resourcepack_id}/preview-image")
async def get_resourcepack_preview_image(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    with open(f'src/api/static/{models_preview_placeholder}', 'rb') as f:
        return Response(content=f.read(), media_type="image/png")


@router.post("", response_model=ResourcepackOut)
async def create_resourcepack(resourcepack: ResourcepackIn, db: Session = Depends(get_db)):
    try:
        print(f'Creating resourcepack: {resourcepack.name}')
        if resourcepack.name is None or resourcepack.name == "":
            raise HTTPException(status_code=400, detail="Resourcepack name cannot be empty")

        if resourcepack.version is None or resourcepack.version == "":
            raise HTTPException(status_code=400, detail="Resourcepack version cannot be empty")

        new_resourcepack = Resourcepack(
            name=resourcepack.name,
            version=resourcepack.version,
            description=resourcepack.description
        )

        models = db.query(Model).filter(Model.id.in_([model.model_id for model in resourcepack.models])).all()
        sounds = db.query(Sound).filter(Sound.id.in_([sound.sound_id for sound in resourcepack.sounds])).all()

        print("query complete")

        if len(models) != len(resourcepack.models) or len(sounds) != len(resourcepack.sounds):
            raise HTTPException(status_code=404, detail="One or more models or sounds not found")

        print("models and sounds found")
        # Add models to the resourcepack and set additional fields
        for model_item in resourcepack.models:
            print(model_item.model_id)
            model_in_db = next((model for model in models if model.id == model_item.model_id), None)
            if model_in_db is not None:
                new_resourcepack.models.append(model_in_db)
                model_in_db.change_type = model_item.change_type
                model_in_db.change_item = model_item.change_item
                model_in_db.custom_model_data = model_item.custom_model_data

        db.add(new_resourcepack)
        db.commit()
        db.refresh(new_resourcepack)

        return new_resourcepack

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create resourcepack")


@router.put("/{resourcepack_id}", response_model=ResourcepackOut)
async def update_resourcepack(resourcepack_id: int, resourcepack: ResourcepackIn, db: Session = Depends(get_db)):
    try:
        db_resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
        if not db_resourcepack:
            raise HTTPException(status_code=404, detail="Resourcepack not found")

        # Update resourcepack fields
        db_resourcepack.name = resourcepack.name
        db_resourcepack.version = resourcepack.version
        db_resourcepack.description = resourcepack.description

        # Clear existing models and sounds associated with the resourcepack
        db.query(resourcepack_models).filter(resourcepack_models.c.resourcepack_id == resourcepack_id).delete()
        db.query(resourcepack_sounds).filter(resourcepack_sounds.c.resourcepack_id == resourcepack_id).delete()

        # Associate updated models and sounds with the resourcepack
        models = db.query(Model).filter(Model.id.in_([model.model_id for model in resourcepack.models])).all()
        sounds = db.query(Sound).filter(Sound.id.in_([sound.sound_id for sound in resourcepack.sounds])).all()

        if len(models) != len(resourcepack.models) or len(sounds) != len(resourcepack.sounds):
            raise HTTPException(status_code=404, detail="One or more models or sounds not found")

        # Add models to the resourcepack and update additional fields
        for model_item in resourcepack.models:
            model_in_db = next((model for model in models if model.id == model_item.model_id), None)
            if model_in_db is not None:
                db_resourcepack.models.append(model_in_db)
                model_in_db.change_type = model_item.change_type
                model_in_db.change_item = model_item.change_item
                model_in_db.custom_model_data = model_item.custom_model_data

        db.commit()
        db.refresh(db_resourcepack)

        return db_resourcepack

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update resourcepack")


@router.delete("/{resourcepack_id}")
async def delete_resourcepack(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    db.delete(resourcepack)
    db.commit()

    return Response(status_code=204)

# Models ----------------------------------------------------------------------

@router.post("/{resourcepack_id}/models", response_model=ResourcepackOut)
async def add_models_to_resourcepack(resourcepack_id: int, models: List[ResourcepackModelItem], db: Session = Depends(get_db)):
    try:
        resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
        if not resourcepack:
            raise HTTPException(status_code=404, detail="Resourcepack not found")

        existing_model_ids = [model.id for model in resourcepack.models]
        for model in models:
            model_in_db = db.query(Model).filter(Model.id == model.model_id).first()
            if model_in_db is None:
                raise HTTPException(status_code=404, detail=f"Model with id {model.model_id} not found")

            if model_in_db.id not in existing_model_ids:
                resourcepack.models.append(model_in_db)
                existing_model_ids.append(model_in_db.id)
            else:
                # Update additional fields for an existing model
                for existing_model in resourcepack.models:
                    if existing_model.id == model_in_db.id:
                        existing_model.change_type = model.change_type
                        existing_model.change_item = model.change_item
                        existing_model.custom_model_data = model.custom_model_data

        db.commit()
        db.refresh(resourcepack)

        return resourcepack

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="One or more models are already associated with the resourcepack")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add models to resourcepack")

from sqlalchemy.orm import Session

@router.put("/{resourcepack_id}/models", response_model=ResourcepackOut)
async def update_resourcepack_models(resourcepack_id: int, models: List[ResourcepackModelItem], db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    existing_model_ids = [model.id for model in resourcepack.models]

    new_models = []
    for model in models:
        model_in_db = db.query(Model).filter(Model.id == model.model_id).first()
        if model_in_db is None:
            raise HTTPException(status_code=404, detail=f"Model with id {model.model_id} not found")
        new_models.append(model_in_db)

    resourcepack.models = new_models

    db.commit()
    db.refresh(resourcepack)

    return resourcepack

@router.delete("/{resourcepack_id}/models", response_model=ResourcepackOut)
async def delete_all_models_from_resourcepack(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    if not resourcepack.models:
        raise HTTPException(status_code=400, detail="Resourcepack does not have any models")

    resourcepack.models.clear()

    db.commit()
    db.refresh(resourcepack)

    return resourcepack

@router.delete("/{resourcepack_id}/models/{model_id}", response_model=ResourcepackOut)
async def delete_model_from_resourcepack(resourcepack_id: int, model_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model not in resourcepack.models:
        raise HTTPException(status_code=400, detail="Model is not associated with the resourcepack")

    resourcepack.models.remove(model)

    db.commit()
    db.refresh(resourcepack)

    return resourcepack

# Sounds ---------------------------------------------------------------- 
@router.get("/{resourcepack_id}/sounds", response_model=List[SoundOut])
async def get_resourcepack_sounds(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    return resourcepack.sounds

@router.post("/{resourcepack_id}/sounds", response_model=ResourcepackOut)
async def add_sound_to_resourcepack(resourcepack_id: int, sound: SoundIn, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    new_sound = Sound(
        name=sound.name,
        description=sound.description
    )

    resourcepack.sounds.append(new_sound)

    db.add(new_sound)
    db.commit()
    db.refresh(resourcepack)

    return resourcepack

@router.put("/{resourcepack_id}/sounds/{sound_id}", response_model=ResourcepackOut)
async def update_sound_in_resourcepack(resourcepack_id: int, sound_id: int, sound: SoundIn, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    sound_in_db = db.query(Sound).filter(Sound.id == sound_id).first()
    if not sound_in_db:
        raise HTTPException(status_code=404, detail="Sound not found")

    sound_in_db.name = sound.name
    sound_in_db.description = sound.description

    db.commit()
    db.refresh(resourcepack)

    return resourcepack

@router.delete("/{resourcepack_id}/sounds/{sound_id}", response_model=ResourcepackOut)
async def delete_sound_from_resourcepack(resourcepack_id: int, sound_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    sound = db.query(Sound).filter(Sound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail="Sound not found")

    if sound not in resourcepack.sounds:
        raise HTTPException(status_code=400, detail="Sound is not associated with the resourcepack")

    resourcepack.sounds.remove(sound)

    db.commit()
    db.refresh(resourcepack)

    return resourcepack

# Сбор ресурсов ---------------------------------------------------------
@router.get("/{resourcepack_id}/file")
async def get_resourcepack(resourcepack_id: int, db: Session = Depends(get_db)):
    resourcepack = db.query(Resourcepack).filter(Resourcepack.id == resourcepack_id).first()
    if not resourcepack:
        raise HTTPException(status_code=404, detail="Resourcepack not found")

    resourcepack_dir = os.path.join(RESOURCEPACKS_DIR, str(resourcepack.id))
    if not os.path.exists(resourcepack_dir):
        os.mkdir(resourcepack_dir)

    assets_dir = os.path.join(resourcepack_dir, 'assets')
    minecraft_dir = os.path.join(assets_dir, 'minecraft')
    textures_dir = os.path.join(minecraft_dir, 'textures')
    models_dir = os.path.join(minecraft_dir, 'models')
    custom_dir = os.path.join(assets_dir, 'custom')

    os.makedirs(textures_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(custom_dir, exist_ok=True)

    # Create pack.mcmeta
    pack_mcmeta_path = os.path.join(resourcepack_dir, 'pack.mcmeta')
    pack_mcmeta_content = {
        "pack": {
            "pack_format": 9,
            "description": resourcepack.description
        }
    }

    with open(pack_mcmeta_path, 'w') as pack_mcmeta_file:
        json.dump(pack_mcmeta_content, pack_mcmeta_file)

    for model in resourcepack.models:
        model_dir = os.path.join(models_dir, model.name)
        os.makedirs(model_dir, exist_ok=True)
        texture_dir = os.path.join(textures_dir, model.name)
        os.makedirs(texture_dir, exist_ok=True)


    for sound in resourcepack.sounds:
        # Generate or copy sound files to the custom directory
        sound_dir = os.path.join(custom_dir, sound.name)
        os.makedirs(sound_dir, exist_ok=True)


    zip_file_path = os.path.join(resourcepack_dir, 'resourcepack.zip')

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(resourcepack_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, resourcepack_dir)
                zip_file.write(file_path, rel_path)

    return Response(zip_file_path)
