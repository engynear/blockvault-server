from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import UploadFile, File
from typing import List

from sqlalchemy.orm import Session

from db.session import get_db, get_s3_client
from db.models import Model
from api.models import ModelIn, ModelOut


router = APIRouter()

@router.get("", response_model=List[ModelOut])
async def get_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    models = db.query(Model).offset(skip).limit(limit).all()
    return models

@router.get("/{model_id}", response_model=ModelOut)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(model)
    db.commit()
    return {"message": "Model deleted"}

@router.put("/{model_id}", response_model=ModelIn)
async def update_model(model_id: int, model: ModelIn, db: Session = Depends(get_db)):
    db_model = db.query(Model).filter(Model.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    update_data = model.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.post("", response_model=ModelIn)
async def create_model(model: ModelIn, db: Session = Depends(get_db)):
    db_model = Model(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.post("/files/bbmodel")
async def upload_bbmodel_file(file: UploadFile = File(...), s3 = Depends(get_s3_client)):
    objects = s3.list_objects(Bucket='model-files')
    async def check_name_available(contents):
        import re
        if file.filename in [obj['Key'] for obj in contents]:
            file.filename, extension = file.filename.split('.')
            print(file.filename)
            if re.search(r'_\d+$', file.filename):
                i = file.filename.split('_')[-1]
                file.filename = file.filename[:-len(i)] + str(int(i) + 1)
            else:
                file.filename += '_1'
            file.filename += f'.{extension}'
            await check_name_available(contents)

    if objects.get('Contents'):
        objects = objects['Contents']
        try:
            await check_name_available(objects)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Something went wrong")

    try:
        s3.upload_fileobj(file.file, 'model-files', file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Problem uploading file to S3")

    return {"file_path": file.filename, "bucket": "model-files"}

@router.post("/files/modelpreview")
async def upload_modelpreview_file(file: UploadFile = File(...), s3 = Depends(get_s3_client)):
    objects = s3.list_objects(Bucket='model-previews')
    async def check_name_available(contents):
        import re
        if file.filename in [obj['Key'] for obj in contents]:
            file.filename, extension = file.filename.split('.')
            print(file.filename)
            if re.search(r'_\d+$', file.filename):
                i = file.filename.split('_')[-1]
                file.filename = file.filename[:-len(i)] + str(int(i) + 1)
            else:
                file.filename += '_1'
            file.filename += f'.{extension}'
            await check_name_available(contents)

    if objects.get('Contents'):
        objects = objects['Contents']
        try:
            await check_name_available(objects)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Something went wrong")

    try:
        s3.upload_fileobj(file.file, 'model-previews', file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Problem uploading file to S3")

    return {"file_path": file.filename, "bucket": "model-previews"}

@router.get("/files/modelpreview/{file_path}")
async def get_modelpreview_file(file_path: str, s3 = Depends(get_s3_client)):
    try:
        obj = s3.get_object(Bucket='model-previews', Key=file_path)
        return Response(content=obj['Body'].read(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")