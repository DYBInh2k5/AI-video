import os
import uuid
import shutil
import asyncio
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from processor import VideoProcessor

app = FastAPI(title="AI Video Translator")

# Priority: BASE_URL env > RENDER_EXTERNAL_URL (Render.com) > Default localhost
BASE_URL = os.getenv("BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "http://localhost:8000"

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "AI Video Translator API is running",
        "endpoints": {
            "upload": "/upload",
            "translate": "/translate",
            "status": "/status/{job_id}",
            "outputs": "/outputs"
        }
    }

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Lazy loading processor to avoid startup delay
processor = None

def get_processor():
    global processor
    if processor is None:
        processor = VideoProcessor()
    return processor

class TranslationRequest(BaseModel):
    video_id: str
    target_language: str
    voice_type: str = "clone" # Default to clone

jobs = {}

async def process_video_task(job_id: str, video_path: str, target_lang: str, voice_type: str):
    try:
        jobs[job_id]["status"] = "processing"
        proc = get_processor()
        
        output_filename = f"{job_id}_translated.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        result = proc.process(video_path, target_lang, output_path, voice_type)
        
        jobs[job_id] = {
            "status": "completed",
            "url": f"{BASE_URL}/outputs/{output_filename}",
            "filename": output_filename,
            "segments": result.get("segments"),
            "transcription": result.get("transcription"),
            "translation": result.get("translation")
        }
    except Exception as e:
        print(f"Error processing video: {e}")
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    print(f"📥 Incoming upload request: {file.filename}")
    try:
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1]
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        jobs[file_id] = {"status": "uploaded", "filename": file.filename}
        print(f"✅ File saved as: {file_path}")
        return {"video_id": file_id}
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def translate_video(request: TranslationRequest, background_tasks: BackgroundTasks):
    if request.video_id not in jobs:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if file exists
    video_path = None
    for ext in ["mp4", "mov", "avi", "mkv"]:
        p = os.path.join(UPLOAD_DIR, f"{request.video_id}.{ext}")
        if os.path.exists(p):
            video_path = p
            break
            
    if not video_path:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    background_tasks.add_task(process_video_task, request.video_id, video_path, request.target_language, request.voice_type)
    return {"job_id": request.video_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
