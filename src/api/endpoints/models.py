from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import UploadFile, File
from typing import List

from sqlalchemy.orm import Session

from db.session import get_db, get_s3_client
from db.models import Model
from api.models.models import ModelIn, ModelOut

models_preview_placeholder = 'models-preview-placeholder.png'

router = APIRouter()

@router.get("", response_model=List[ModelOut])
async def get_models(skip: int = 0, limit: int = None, db: Session = Depends(get_db)):
    models = db.query(Model).offset(skip).limit(limit).all()
    return models

@router.get("/{model_id}", response_model=ModelOut)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    return model

@router.post("", response_model=ModelOut)
async def create_model(model: ModelIn, db: Session = Depends(get_db)):
    db_model = Model(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.put("/{model_id}", response_model=ModelOut)
async def update_model(model_id: int, model: ModelIn, db: Session = Depends(get_db)):
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    update_data = model.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')

    bucket_name = 'blockvault-bucket'
    objects = s3.list_objects(Bucket=bucket_name, Prefix=f'models/model_{model_id}')
    if 'Contents' in objects:
        for obj in objects['Contents']:
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])

    db.delete(model)
    db.commit()
    return {"message": f'Model {model_id} deleted'}

@router.get("/{model_id}/preview-image")
async def get_model_preview_image(model_id: int, db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    bucket_name = 'blockvault-bucket'
    try:
        image = s3.get_object(Bucket=bucket_name, Key=f'models/model_{model_id}/preview.png')
    except Exception as e:
        with open(f'src/api/static/{models_preview_placeholder}', 'rb') as f:
            return Response(content=f.read(), media_type="image/png")
    return Response(content=image['Body'].read(), media_type="image/png")

@router.post("/{model_id}/preview-image")
async def upload_model_preview_image(model_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    if file.content_type != 'image/png':
        raise HTTPException(status_code=400, detail=f'Preview image must be a png file')

    bucket_name = 'blockvault-bucket'
    s3.put_object(Bucket=bucket_name, Key=f'models/model_{model_id}/preview.png', Body=file.file.read())
    return {"message": f'Preview image for model {model_id} uploaded'}


@router.put("/{model_id}/preview-image")
async def update_model_preview_image(model_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    if file.content_type != 'image/png':
        raise HTTPException(status_code=400, detail=f'Preview image must be a png file')

    bucket_name = 'blockvault-bucket'
    s3.put_object(Bucket=bucket_name, Key=f'models/model_{model_id}/preview.png', Body=file.file.read())
    return {"message": f'Preview image for model {model_id} updated'}

@router.get("/{model_id}/project")
async def get_bbmodel_file(model_id: int, db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    bucket_name = 'blockvault-bucket'
    try:
        file = s3.get_object(Bucket=bucket_name, Key=f'models/model_{model_id}/project.bbmodel')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail=f'BBModel file for model {model_id} not found')
    return Response(content=file['Body'].read(), media_type="application/octet-stream")

@router.post("/{model_id}/project")
async def upload_bbmodel_file(model_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    if file.content_type != 'application/octet-stream' or not file.filename.endswith('.bbmodel'):
        raise HTTPException(status_code=400, detail=f'Project file must be a bbmodel file')

    bucket_name = 'blockvault-bucket'
    s3.put_object(Bucket=bucket_name, Key=f'models/model_{model_id}/project.bbmodel', Body=file.file.read())
    return {"message": f'BBModel file for model {model_id} uploaded'}

@router.put("/{model_id}/project")
async def update_bbmodel_file(model_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail=f'Model {model_id} not found')
    
    if file.content_type != 'application/octet-stream' or not file.filename.endswith('.bbmodel'):
        raise HTTPException(status_code=400, detail=f'Project file must be a bbmodel file')

    bucket_name = 'blockvault-bucket'
    s3.put_object(Bucket=bucket_name, Key=f'models/model_{model_id}/project.bbmodel', Body=file.file.read())
    return {"message": f'BBModel file for model {model_id} updated'}