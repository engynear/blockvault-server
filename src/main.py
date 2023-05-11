from fastapi import FastAPI
from sqlalchemy import create_engine

from db.base import Base, create_s3_buckets
from db.models import Model, Sound, Map

from api.endpoints import models, resourcepacks, sounds
from core.config import settings

from fastapi.middleware.cors import CORSMiddleware


engine = create_engine(settings.DATABASE_URL)
Base.metadata.create_all(bind=engine)
create_s3_buckets()



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(resourcepacks.router, prefix="/resourcepacks", tags=["resourcepacks"])
app.include_router(sounds.router, prefix="/sounds", tags=["sounds"])

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)