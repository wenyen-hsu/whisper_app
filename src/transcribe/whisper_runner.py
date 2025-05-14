"""
Whisper.cpp Python binding wrapper for local transcription.
"""
from typing import Optional, Dict, Any  # 型別註解
import os  # 作業系統操作
import subprocess  # 直接呼叫 ffmpeg 並捕捉 stderr
import soundfile as sf  # 讀取 wav 檔
import numpy as np
from whispercpp import Whisper  # Whisper.cpp 綁定
import logging
import tempfile

MODEL_PATH = os.getenv("WHISPER_MODEL_PATH", "medium")  # 讀取模型路徑環境變數

class WhisperTranscriber:
    def __init__(self, model_path: str = MODEL_PATH):  # 初始化
        self.model_path = model_path  # 設定模型路徑
        self.whisper = Whisper.from_pretrained(model_path)  # 載入本地模型

    def preprocess_audio(self, input_path: str, output_path: str) -> str:
        """Convert audio to 16kHz mono wav for whisper.cpp. 若失敗則回傳 ffmpeg stderr 訊息。"""
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "16000", "-ac", "1", "-f", "wav", output_path
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err_msg = proc.stderr.decode(errors="ignore")
            raise RuntimeError(f"ffmpeg error: {err_msg}")
        return output_path  # 回傳輸出路徑

    def _segments_to_srt(self, segments):
        def format_time(seconds):
            ms = int((seconds - int(seconds)) * 1000)
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"
        text = ""
        for idx, seg in enumerate(segments, 1):
            start = format_time(seg.get("start", 0))
            end = format_time(seg.get("end", 0))
            seg_text = seg.get("text", "")
            text += f"{idx}\n{start} --> {end}\n{seg_text}\n\n"
        return text

    def transcribe(self, audio_path: str, lang: Optional[str] = None):
        import langdetect
        import shutil
        # 使用 whisper.cpp CLI 進行翻譯或原文輸出
        with tempfile.TemporaryDirectory() as tmpdir:
            # 先將音檔轉成 16kHz 單聲道 PCM wav
            converted_path = os.path.join(tmpdir, "converted.wav")
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", audio_path,
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", converted_path
            ]
            try:
                subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                logging.error(f"[WhisperTranscriber] ffmpeg 轉檔失敗: {e}")
                raise RuntimeError(f"ffmpeg 轉檔失敗: {e}")

            output_base = os.path.join(tmpdir, "result")
            # 若 self.model_path 不是絕對路徑，嘗試自動補全
            model_path = self.model_path
            if not os.path.isabs(model_path) and not os.path.exists(model_path):
                home = os.path.expanduser("~")
                candidate = os.path.join(home, ".local/share/whispercpp", f"ggml-{model_path}.bin")
                if os.path.exists(candidate):
                    model_path = candidate
            # 語言偵測（可選）
            detected_lang = None
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.AudioFile(converted_path) as source:
                    audio = r.record(source)
                detected_lang = r.recognize_google(audio, show_all=True)
            except Exception as e:
                logging.warning(f"[WhisperTranscriber] 語音語言偵測失敗: {e}")
            # 組合 CLI 參數
            cmd = [
                "./whisper.cpp/build/bin/whisper-cli",
                converted_path,
                "--model", model_path,
                "--output-txt",
                "--output-srt",
                "--output-file", output_base
            ]
            if lang:
                cmd += ["--language", lang]
                if lang != "en":
                    cmd += ["--translate"]
            else:
                if detected_lang and not (isinstance(detected_lang, str) and detected_lang.startswith("en")):
                    cmd += ["--translate"]
            logging.info(f"[WhisperTranscriber] CLI 參數: {' '.join(cmd)}")
            try:
                subprocess.run(cmd, check=True)
            except Exception as e:
                logging.error(f"[WhisperTranscriber] whisper.cpp CLI 執行失敗: {e}")
                raise
            # 讀取 txt 結果
            txt_path = output_base + ".txt"
            srt_path = output_base + ".srt"
            text = ""
            srt = ""
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    text = f.read()
            if os.path.exists(srt_path):
                with open(srt_path, "r", encoding="utf-8") as f:
                    srt = f.read()
            return {
                "text": text,
                "srt": srt,
                "segments": [],
            }
