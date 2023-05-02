import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from models import Model, ModelPayload

app = FastAPI()
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

import os

from botocore.utils import fix_s3_host
import boto3

os.environ['AWS_ACCESS_KEY_ID'] = "accessKey1"
os.environ['AWS_SECRET_ACCESS_KEY'] = "verySecretKey1"
s3 = boto3.resource(service_name='s3', endpoint_url='http://localhost:8000')
s3.meta.client.meta.events.unregister('before-sign.s3', fix_s3_host)

import psycopg2
conn = psycopg2.connect(
    host="localhost",
    database="blockvault",
    user="engynear",
    password="132wersdf"
)
cur = conn.cursor()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):
    # Сохраняем файл на диск
    with open(file.filename, "wb") as f:
        f.write(await file.read())
    
    return {"filename": file.filename}

# @app.post("/models")
# async def upload_model(payload: ModelPayload = None):
#     print(payload)
#     modelName = payload.modelName
#     modelType = payload.modelType
#     modelTags = payload.modelTags
#     modelFile = payload.modelFile
#     previewImage = payload.previewImage
#     # print(title)
#     # pass
#     # return 200
#     # сохраняем файлы модели и изображения на сервере
#     contents_model = await modelFile.read()
#     filename_model = modelFile.filename
#     # save model file to disk
#     with open(filename_model, "wb") as f:
#         f.write(contents_model)

    
#     contents_image = await previewImage.read()
#     filename_image = previewImage.filename
#     # save image file to disk
#     with open(filename_image, "wb") as f:
#         f.write(contents_image)
    
#     # # делаем что-то с полученными данными
#     result = {'modelName': modelName, 'modelType': modelType, 'modelFile': filename_model, 'previewImage': filename_image, 'modelTags': modelTags}
#     return result, 200

@app.get("/downloadfile/{file_path:path}")
async def read_uploaded_file(file_path: str):
    return FileResponse(file_path)

@app.get("/models/{id}")
async def get_model(id: int):
    cur.execute(f"SELECT * FROM models WHERE id={id}")
    row = cur.fetchone()
    print(row)

    model = {
        "id": row[0],
        "name": row[1],
        "preview_path": row[2],
        "type": row[3],
        "tags": row[4]
    }

    return model

@app.get("/models/{id}/preview")
async def get_model_preview(id: int):
    obj = s3.Object('modelpreview', f'{id}.png')
    content = obj.get()['Body'].read()
    headers = {
        "Content-Type": "image/png",
        "Content-Disposition": "attachment; filename=preview.png"
    }
    return Response(content, media_type="image/png", headers=headers)


@app.get("/models", response_model=List[Model])
async def get_models():
    # выполнение запроса на выборку всех моделей
    cur = conn.cursor()
    cur.execute("SELECT * FROM models")
    rows = cur.fetchall()

    print(rows)
    models = []
    for row in rows:
        model = {
            "id": row[0],
            "name": row[1],
            "preview_path": row[2],
            "type": row[3],
            "tags": row[4]
        }
        models.append(model)

    return models

@app.get("/filelist/")
async def return_file_list():
    bucket = s3.Bucket('bucket1')
    filesList = []
    for obj in bucket.objects.all():
        filesList.append(obj.key)

    return filesList
        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)