from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import UploadFile, File
from typing import List

from sqlalchemy.orm import Session

from db.session import get_db, get_s3_client
from db.models import Sound
from api.models.sounds import SoundIn, SoundOut

router = APIRouter()

@router.get("", response_model=List[SoundOut])
async def get_sounds(skip: int = 0, limit: int = None, db: Session = Depends(get_db)):
    sounds = db.query(Sound).offset(skip).limit(limit).all()
    return sounds

@router.get("/{sound_id}", response_model=SoundOut)
async def get_sound(sound_id: int, db: Session = Depends(get_db)):
    sound = db.query(Sound).filter(Sound.id == sound_id).first()
    if sound is None:
        raise HTTPException(status_code=404, detail="Sound not found")
    return sound

@router.post("", response_model=SoundOut)
async def create_sound(sound: SoundIn, db: Session = Depends(get_db)):
    db_sound = Sound(**sound.dict())
    db.add(db_sound)
    db.commit()
    db.refresh(db_sound)
    return db_sound


@router.post("/{sound_id}/clip", response_model=SoundOut)
async def upload_sound_clip(sound_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    sound = db.query(Sound).filter(Sound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail=f'Sound {sound_id} not found')
    
    if not file.filename.lower().endswith('.wav'):
        raise HTTPException(status_code=400, detail='Sound clip must be a WAV file')
    
    bucket_name = 'blockvault-bucket'
    s3_key = f'sounds/sound_{sound_id}.wav'
    s3.put_object(Bucket=bucket_name, Key=s3_key, Body=await file.read())
    
    return sound

@router.get("/{sound_id}/clip")
async def get_sound_clip(sound_id: int, db: Session = Depends(get_db), s3 = Depends(get_s3_client)):
    sound = db.query(Sound).filter(Sound.id == sound_id).first()
    if not sound:
        raise HTTPException(status_code=404, detail=f'Sound {sound_id} not found')
    
    bucket_name = 'blockvault-bucket'
    s3_key = f'sounds/sound_{sound_id}.wav'
    
    try:
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        clip_data = response['Body'].read()
        return Response(content=clip_data, media_type='audio/wav')
    except Exception as e:
        raise HTTPException(status_code=404, detail=f'Sound clip for sound {sound_id} not found')