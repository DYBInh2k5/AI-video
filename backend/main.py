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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domains
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

jobs = {}

async def process_video_task(job_id: str, video_path: str, target_lang: str):
    try:
        jobs[job_id]["status"] = "processing"
        proc = get_processor()
        
        output_filename = f"{job_id}_translated.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        proc.process(video_path, target_lang, output_path)
        
        jobs[job_id] = {
            "status": "completed",
            "url": f"{BASE_URL}/outputs/{output_filename}",
            "filename": output_filename
        }
    except Exception as e:
        print(f"Error processing video: {e}")
        jobs[job_id] = {"status": "failed", "error": str(e)}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_extension}")
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    jobs[file_id] = {"status": "uploaded", "filename": file.filename}
    return {"video_id": file_id}

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
    
    background_tasks.add_task(process_video_task, request.video_id, video_path, request.target_language)
    return {"job_id": request.video_id, "status": "queued"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    return jobs.get(job_id, {"status": "not_found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
