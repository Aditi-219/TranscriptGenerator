# 🎙️ BoliScript - Hindi Video Transcript Generator
A mobile-first, lightweight web application to generate accurate Hindi (Devanagari) transcripts and optional English translations from **YouTube** (Videos & Shorts) and **Facebook** (Reels & Videos).

---

## ✨ Features
- 📱 **Mobile-Optimized UI**: Designed specifically for mobile screens with touch-friendly buttons, paste-from-clipboard, font scaling, and smooth tab navigation.
- 🇮🇳 **High-Accuracy Hindi Transcription**: High-fidelity Devanagari script output powered by **Groq Whisper-large-v3** (blazing fast, 3-8 seconds) or **Google Gemini 2.0 Flash**.
- 🌐 **YouTube & Facebook Support**: Handles YouTube videos, YouTube Shorts, Facebook Watch videos, and Facebook Reels.
- 🕒 **Segment Timestamps**: Interactive timestamps for each dialogue segment. Click any snippet to copy it with its timestamp.
- 🔤 **English Translation Option**: Toggle on to generate a simultaneous side-by-side English translation.
- 💾 **Export Options**: One-tap copy, download as formatted `.txt`, or download as subtitle `.srt` format.
- 🔒 **Zero Friction / Privacy Friendly**: Store your API key right inside your mobile browser's localStorage or set it in the server's `.env`.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (Verified on Python 3.13)
- Internet connection

### 2. Start the Server
Run the startup script in terminal / PowerShell:
```powershell
py -3.13 run.py
```
*(Or `python run.py`)*

### 3. Open on Mobile Phone
1. Ensure your mobile phone is connected to the same Wi-Fi network as your computer.
2. Find your computer's local IP address (run `ipconfig` in cmd/PowerShell, look for `IPv4 Address`, e.g. `192.168.1.15`).
3. Open mobile browser (Chrome/Safari) and go to:
   ```
   http://192.168.1.XX:8000
   ```
*(To test locally on PC, visit `http://localhost:8000`)*

---

## 🔑 Getting an API Key (Free)
You can use either **Groq** (Recommended for speed) or **Google Gemini**:

### Option A: Groq Whisper (Recommended - 5 seconds processing)
1. Go to [Groq Console](https://console.groq.com/keys).
2. Sign in with Google / GitHub.
3. Click **"Create API Key"** and copy the key (starts with `gsk_...`).
4. Paste the key in the web app's **Settings (⚙️)** or add `GROQ_API_KEY=gsk_...` in `.env`.

### Option B: Google Gemini
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **"Get API key"**.
3. Paste the key in Settings (⚙️) or add `GEMINI_API_KEY=AIza...` in `.env`.

---

## 📁 Project Structure
```
TranscriptGenerator/
├── backend/
│   ├── downloader.py    # yt-dlp & imageio-ffmpeg audio extraction
│   ├── transcriber.py   # Groq Whisper & Gemini 2.0 Flash integration
│   └── main.py          # FastAPI application & REST endpoints
├── static/
│   ├── index.html       # Mobile-first responsive UI
│   ├── style.css        # Animations & scrollbars
│   └── app.js           # Client logic, clipboard, downloads
├── requirements.txt     # Python packages
├── run.py               # Launcher script
└── .env.example         # Environment template
```
