from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import os
import shutil
import cloudinary
import cloudinary.uploader
from utils.transcriber import transcribe_video
from utils.segmenter import segment_transcript
from utils.clipper import clip_video_from_text

# Configure Cloudinary
cloudinary.config(
    cloud_name="dnr6jc1yr",
    api_key="187812252132193",
    api_secret="a1JcGtsy2sTS_jQzCd7t_6kemx0"
)

# Temporary directory for processing
TEMP_DIR = "./temp"
os.makedirs(TEMP_DIR, exist_ok=True)

def upload_to_cloudinary(video_path):
    """Uploads a video file to Cloudinary and returns the URL."""
    response = cloudinary.uploader.upload(video_path, resource_type="video")
    return response["secure_url"]

app = FastAPI()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Save the uploaded video temporarily
        temp_video_path = os.path.join(TEMP_DIR, file.filename)
        with open(temp_video_path, "wb") as temp_video:
            shutil.copyfileobj(file.file, temp_video)

        # Transcribe and segment
        transcript, timestamps = transcribe_video(temp_video_path, TEMP_DIR)
        segments = segment_transcript(transcript, timestamps, min_duration=30.0, refine_with_ai=False)
        clipped_videos = clip_video_from_text(temp_video_path, segments, TEMP_DIR)

        # Upload clipped videos to Cloudinary
        cloudinary_urls = [upload_to_cloudinary(clip) for clip in clipped_videos]

        # Remove temp files
        os.remove(temp_video_path)
        for clip in clipped_videos:
            os.remove(clip)

        return JSONResponse(content={"segments": segments, "video_urls": cloudinary_urls})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
