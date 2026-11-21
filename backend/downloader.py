import os
import re
import tempfile
import uuid
import shutil
import urllib.parse
import yt_dlp
import imageio_ffmpeg

FFMPEG_EXE = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

def normalize_video_url(url: str) -> str:
    """Unwraps Facebook login redirect and share tracking wrappers to get the actual video/reel URL."""
    url = url.strip()
    if 'facebook.com/login' in url.lower() or 'share_url=' in url:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'next' in qs:
                next_url = qs['next'][0]
                next_parsed = urllib.parse.urlparse(next_url)
                next_qs = urllib.parse.parse_qs(next_parsed.query)
                if 'share_url' in next_qs:
                    return next_qs['share_url'][0]
                return next_url
            if 'share_url' in qs:
                return qs['share_url'][0]
        except Exception:
            pass
    return url

def detect_platform(url: str) -> str:
    clean_url = normalize_video_url(url)
    lower = clean_url.lower()
    if "youtu.be" in lower or "youtube.com" in lower:
        return "youtube"
    elif "facebook.com" in lower or "fb.watch" in lower or "fb.com" in lower:
        return "facebook"
    return "other"

def get_video_info(url: str) -> dict:
    url = normalize_video_url(url)
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'web']
            }
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Video"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail") or (info.get("thumbnails")[-1]["url"] if info.get("thumbnails") else None),
            "uploader": info.get("uploader") or info.get("channel", "Unknown"),
            "platform": detect_platform(url)
        }

def download_audio(url: str) -> dict:
    """
    Downloads and converts video audio to lightweight MP3 format (optimized for speech transcription).
    Returns path to audio file and metadata.
    """
    url = normalize_video_url(url)
    unique_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(TEMP_DIR, f"{unique_id}_%(title).50s.%(ext)s")
    
    ydl_opts = {
        'format': 'ba/b',
        'ffmpeg_location': FFMPEG_EXE,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb', 'web']
            }
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '64', # 64kbps mono/stereo is ideal for speech and keeps file size tiny
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Identify downloaded mp3 file
        title = info.get("title", "Video")
        duration = info.get("duration", 0)
        thumbnail = info.get("thumbnail")
        uploader = info.get("uploader") or info.get("channel", "Unknown")
        
        # Locate generated file
        expected_base = ydl.prepare_filename(info)
        mp3_file = os.path.splitext(expected_base)[0] + ".mp3"
        
        if not os.path.exists(mp3_file):
            # Fallback search in temp dir for files starting with unique_id
            for f in os.listdir(TEMP_DIR):
                if f.startswith(unique_id) and f.endswith(".mp3"):
                    mp3_file = os.path.join(TEMP_DIR, f)
                    break
        
        if not os.path.exists(mp3_file):
            raise FileNotFoundError(f"Could not locate extracted audio file for {url}")
            
        file_size_mb = os.path.getsize(mp3_file) / (1024 * 1024)
        
        return {
            "file_path": mp3_file,
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "platform": detect_platform(url),
            "file_size_mb": round(file_size_mb, 2)
        }

def cleanup_file(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Warning: Failed to delete {path}: {e}")
