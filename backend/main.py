import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.downloader import download_audio, get_video_info, cleanup_file
from backend.transcriber import transcribe_with_groq, transcribe_with_gemini

app = FastAPI(title="Hindi Video Transcript Generator")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

class InfoRequest(BaseModel):
    url: str

class TranscribeRequest(BaseModel):
    url: str
    engine: Optional[str] = "groq" # "groq" or "gemini"
    api_key: Optional[str] = None
    translate: Optional[bool] = False

@app.get("/api/config")
def get_config():
    """Returns availability of pre-configured server keys without leaking the keys."""
    return {
        "has_groq_key": bool(os.getenv("GROQ_API_KEY")),
        "has_gemini_key": bool(os.getenv("GEMINI_API_KEY"))
    }

@app.post("/api/info")
def fetch_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    try:
        info = get_video_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video details: {str(e)}")

@app.post("/api/transcribe")
def transcribe_video(req: TranscribeRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Video URL is required")
    
    engine = req.engine.lower() if req.engine else "groq"
    
    # Determine API key (Client provided or Server environment variable)
    api_key = req.api_key.strip() if req.api_key else None
    if not api_key:
        if engine == "groq":
            api_key = os.getenv("GROQ_API_KEY")
        elif engine == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            
    if not api_key:
        engine_name = "Groq" if engine == "groq" else "Google Gemini"
        raise HTTPException(
            status_code=400, 
            detail=f"Missing {engine_name} API Key. Please provide one in Settings or set {engine.upper()}_API_KEY on the server."
        )

    # 1. Download and convert audio to speech-optimized MP3
    audio_meta = None
    try:
        audio_meta = download_audio(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audio download failed: {str(e)}")

    mp3_path = audio_meta["file_path"]
    
    # 2. Transcribe Hindi speech using cloud engine
    try:
        if engine == "gemini":
            result = transcribe_with_gemini(mp3_path, api_key, translate_to_english=bool(req.translate))
        else:
            result = transcribe_with_groq(mp3_path, api_key, translate_to_english=bool(req.translate))
            
        # Combine video metadata with transcription result
        return {
            "success": True,
            "title": audio_meta.get("title"),
            "uploader": audio_meta.get("uploader"),
            "thumbnail": audio_meta.get("thumbnail"),
            "duration": audio_meta.get("duration"),
            "platform": audio_meta.get("platform"),
            "engine": result.get("engine"),
            "hindi_transcript": result.get("hindi_transcript"),
            "english_transcript": result.get("english_transcript"),
            "segments": result.get("segments", []),
            "srt_hindi": result.get("srt_hindi", ""),
            "srt_english": result.get("srt_english", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Guarantee audio cleanup to save disk space
        if audio_meta and audio_meta.get("file_path"):
            cleanup_file(audio_meta["file_path"])

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Mobile frontend index.html not yet initialized"}
