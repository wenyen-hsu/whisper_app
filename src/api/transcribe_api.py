"""
FastAPI router for audio upload and transcription.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form, Query
from fastapi.responses import JSONResponse
from typing import Optional
import os
import shutil
from src.transcribe.whisper_runner import WhisperTranscriber
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_TYPES = [
    "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "video/mp4", "audio/mp4", "audio/x-m4a", "audio/m4a", "audio/webm"
]

@router.get("/list_dirs")
def list_dirs(base: Optional[str] = Query("uploads/")):
    """列出 base 目錄下所有子目錄（遞迴）。"""
    result = []
    for root, dirs, files in os.walk(base):
        for d in dirs:
            rel_path = os.path.relpath(os.path.join(root, d), start=base)
            result.append(os.path.join(base, rel_path))
    return {"status": "success", "dirs": result}

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    save_path: Optional[str] = Form(None),
    language: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
):
    if file.content_type not in SUPPORTED_TYPES:
        return JSONResponse(status_code=400, content={"status": "error", "message": "不支援的音訊/影片格式"})
    if file.size and file.size > 500 * 1024 * 1024:
        return JSONResponse(status_code=400, content={"status": "error", "message": "檔案超過 500MB 限制"})

    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        if file.content_type == "audio/webm":
            ext = ".webm"
        elif file.content_type in ("audio/wav", "audio/x-wav"):
            ext = ".wav"
        elif file.content_type in ("audio/mp3", "audio/mpeg"):
            ext = ".mp3"
        elif file.content_type in ("audio/m4a", "audio/x-m4a", "audio/mp4", "video/mp4"):
            ext = ".m4a"
        else:
            ext = ".dat"
    unique_id = uuid.uuid4().hex
    base_filename = f"record_{unique_id}{ext}"
    temp_path = os.path.join(UPLOAD_DIR, base_filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    wav_path = os.path.join(UPLOAD_DIR, f"record_{unique_id}_converted.wav")
    transcriber = WhisperTranscriber()
    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
        return JSONResponse(status_code=400, content={"status": "error", "message": "上傳檔案為空或不存在"})

    try:
        transcriber.preprocess_audio(temp_path, wav_path)
    except Exception as e:
        if os.path.exists(wav_path):
            os.remove(wav_path)
        return JSONResponse(status_code=500, content={"status": "error", "message": f"音訊預處理失敗: {str(e)}"})

    if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
        return JSONResponse(status_code=500, content={"status": "error", "message": "音訊轉檔失敗，產生的 wav 檔案為空，請確認上傳檔案格式與內容。"})

    try:
        result = transcriber.transcribe(wav_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"語音轉錄失敗: {str(e)}"})

    saved_files = {}
    if save_path:
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        text_path = save_path + ".txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(result.get("text", ""))
        saved_files["text"] = text_path
        srt_path = save_path + ".srt"
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(result.get("srt", ""))
        saved_files["srt"] = srt_path

    background_tasks.add_task(os.remove, temp_path)
    background_tasks.add_task(os.remove, wav_path)

    return {"status": "success", "data": result, "saved_files": saved_files}
