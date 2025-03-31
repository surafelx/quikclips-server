from fastapi import APIRouter, UploadFile, File, Form
from api.schemas import ClippingRequest
from utils.transcriber import transcribe_audio
from utils.clipper import generate_clips
import os
import shutil

router = APIRouter()

temp_dir = "temp_videos"
os.makedirs(temp_dir, exist_ok=True)

@router.post("/upload")
async def upload_video(file: UploadFile = File(...),
                       min_duration: int = Form(...),
                       max_duration: int = Form(...),
                       num_clips: int = Form(...),
                       suggestion_prompt: str = Form(None)):
    request = ClippingRequest(
        min_duration=min_duration,
        max_duration=max_duration,
        num_clips=num_clips,
        suggestion_prompt=suggestion_prompt
    )
    
    temp_audio_path = os.path.join(temp_dir, file.filename)
    with open(temp_audio_path, "wb") as temp_audio:
        shutil.copyfileobj(file.file, temp_audio)

    transcript = transcribe_audio(temp_audio_path)
    clip_segments = generate_clips(transcript, request)

    os.remove(temp_audio_path)

    return {"segments": clip_segments}
