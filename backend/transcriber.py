import os
import json
import base64
import requests

def format_timestamp(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{mins:02d}:{secs:02d}"

def seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_srt(segments: list, lang_key: str = "hindi") -> str:
    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seconds_to_srt_time(seg.get("start", 0))
        end = seconds_to_srt_time(seg.get("end", 0))
        text = seg.get(lang_key) or seg.get("text", "")
        srt_lines.append(f"{i}\n{start} --> {end}\n{text.strip()}\n")
    return "\n".join(srt_lines)

def transcribe_with_groq(file_path: str, api_key: str, translate_to_english: bool = False) -> dict:
    """
    Transcribes audio using Groq's whisper-large-v3 model.
    """
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f, "audio/mpeg")
        }
        data = {
            "model": "whisper-large-v3",
            "language": "hi",
            "response_format": "verbose_json",
            "temperature": "0.0",
            "prompt": "यह स्पष्ट और प्रामाणिक हिंदी बातचीत/भाषण है। कृपया हर एक शब्द, संवाद और वाक्य को बिना छोड़े पूरी तरह से शुद्ध देवनागरी लिपि में लिखें।"
        }
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        
    if response.status_code != 200:
        error_msg = response.text
        try:
            err_json = response.json()
            error_msg = err_json.get("error", {}).get("message", error_msg)
        except Exception:
            pass
        raise RuntimeError(f"Groq Whisper API error ({response.status_code}): {error_msg}")
        
    res_data = response.json()
    raw_segments = res_data.get("segments", [])
    full_hindi_text = res_data.get("text", "").strip()
    
    segments = []
    seg_texts = []
    for s in raw_segments:
        start_sec = s.get("start", 0.0)
        end_sec = s.get("end", 0.0)
        text = s.get("text", "").strip()
        if text:
            seg_texts.append(text)
        segments.append({
            "start": round(start_sec, 2),
            "end": round(end_sec, 2),
            "start_formatted": format_timestamp(start_sec),
            "end_formatted": format_timestamp(end_sec),
            "hindi": text,
            "english": ""
        })

    # Ensure full transcript preserves all segment speech without skipping
    joined_segments_text = " ".join(seg_texts).strip()
    if len(joined_segments_text) > len(full_hindi_text):
        full_hindi_text = joined_segments_text
        
    english_transcript = ""
    
    # If translation is requested, use Groq's fast LLM to translate the Hindi transcript
    if translate_to_english and full_hindi_text:
        try:
            trans_url = "https://api.groq.com/openai/v1/chat/completions"
            trans_headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            trans_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in Hindi to English translation. Translate the provided Hindi text into natural, accurate English. Maintain paragraph flow and meaning. Respond ONLY with the English translation."
                    },
                    {
                        "role": "user",
                        "content": full_hindi_text
                    }
                ],
                "temperature": 0.3
            }
            trans_resp = requests.post(trans_url, headers=trans_headers, json=trans_payload, timeout=60)
            if trans_resp.status_code == 200:
                english_transcript = trans_resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            english_transcript = f"(Translation failed: {str(e)})"
            
    srt_hindi = generate_srt(segments, "hindi")
    srt_english = ""
    
    return {
        "engine": "groq",
        "hindi_transcript": full_hindi_text,
        "english_transcript": english_transcript,
        "segments": segments,
        "srt_hindi": srt_hindi,
        "srt_english": srt_english
    }

def transcribe_with_gemini(file_path: str, api_key: str, translate_to_english: bool = False) -> dict:
    """
    Transcribes Hindi audio using Google Gemini 2.0 Flash / 1.5 Flash via REST API.
    """
    # Read and base64 encode audio
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > 20:
        raise ValueError("Audio file exceeds 20MB inline limit for Gemini API. Please use Groq Whisper or shorter video.")
        
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"
    
    prompt = (
        "You are an expert Hindi audio transcriber. Listen carefully to the attached audio, which contains spoken Hindi. "
        "Perform a 100% complete, verbatim transcription of ALL spoken Hindi in clean Devanagari script from the very beginning to the very end. "
        "CRITICAL: Do not skip, omit, summarize, or condense ANY spoken sentence or dialogue. Transcribe every word accurately. "
        "If the speaker uses common English/Hinglish terms, transcribe them appropriately. "
        f"{'Also translate the full transcript into natural English. ' if translate_to_english else ''}"
        "Format your response strictly as valid JSON with the following structure:\n"
        "{\n"
        '  "hindi_transcript": "Full complete verbatim text in Devanagari script with natural paragraphs",\n'
        f'  "english_transcript": "{"Full English translation" if translate_to_english else ""}",\n'
        '  "segments": [\n'
        '     {"start": 0.0, "end": 4.5, "hindi": "...", "english": "..."}\n'
        '  ]\n'
        "}\n"
        "Do not include markdown ticks (```json) or commentary. Return ONLY the raw JSON object."
    )
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "audio/mp3",
                            "data": b64_audio
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    response = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=180)
    
    if response.status_code != 200:
        # Fallback to gemini-2.5-flash or gemini-flash-latest if 3.8-flash is unavailable
        for fallback_model in ["gemini-2.5-flash", "gemini-flash-latest"]:
            fb_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{fallback_model}:generateContent?key={api_key}"
            response = requests.post(fb_endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=180)
            if response.status_code == 200:
                break
        
    if response.status_code != 200:
        error_msg = response.text
        try:
            err_json = response.json()
            error_msg = err_json.get("error", {}).get("message", error_msg)
        except Exception:
            pass
        raise RuntimeError(f"Gemini API error ({response.status_code}): {error_msg}")
        
    result_json = response.json()
    candidates = result_json.get("candidates", [])
    if not candidates:
        raise RuntimeError("No transcription candidates returned by Gemini.")
        
    text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
    
    try:
        # Clean potential markdown fences
        clean_text = text_content.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        parsed = json.loads(clean_text.strip())
    except Exception:
        # If parsing fails, treat the whole response as transcript
        parsed = {
            "hindi_transcript": text_content,
            "english_transcript": "",
            "segments": []
        }
        
    segments = parsed.get("segments", [])
    for seg in segments:
        start_sec = float(seg.get("start", 0.0))
        end_sec = float(seg.get("end", 0.0))
        seg["start_formatted"] = format_timestamp(start_sec)
        seg["end_formatted"] = format_timestamp(end_sec)
        
    srt_hindi = generate_srt(segments, "hindi") if segments else ""
    srt_english = generate_srt(segments, "english") if segments and translate_to_english else ""
    
    return {
        "engine": "gemini",
        "hindi_transcript": parsed.get("hindi_transcript", ""),
        "english_transcript": parsed.get("english_transcript", ""),
        "segments": segments,
        "srt_hindi": srt_hindi,
        "srt_english": srt_english
    }
