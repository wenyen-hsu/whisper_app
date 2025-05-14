"""
Whisper.cpp Python binding wrapper for local transcription.
"""
from typing import Optional, Dict, Any  # 型別註解
import os  # 作業系統操作
import subprocess  # 直接呼叫 ffmpeg 並捕捉 stderr
import soundfile as sf  # 讀取 wav 檔
import numpy as np
from whispercpp import Whisper  # Whisper.cpp 綁定

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

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file using whisper.cpp."""
        # 讀取 wav 檔案內容為 float32 numpy array
        data, samplerate = sf.read(audio_path, dtype='float32')
        print(f"[DEBUG] 讀取音訊: {audio_path}, 取樣率: {samplerate}, 資料長度: {len(data)}")
        if len(data.shape) > 1:
            data = data[:, 0]  # 只取第一個 channel（保險起見）
        data = data.tolist()
        # 僅帶 return_segments 參數，不帶 task 參數，確保以原語言輸出
        result = self.whisper.transcribe(data)
        print(f"[DEBUG] whisper.transcribe 回傳: {result}")
        if isinstance(result, str):
            print(f"[DEBUG] 辨識結果為 str: {result}")
            return {
                "srt": "",
                "text": result,
                "segments": [],
            }
        print(f"[DEBUG] SRT: {result.get('srt', '')[:100]}...")
        print(f"[DEBUG] text: {result.get('text', '')[:100]}...")
        print(f"[DEBUG] segments 數量: {len(result.get('segments', []))}")
        if len(result.get('segments', [])) > 0:
            print(f"[DEBUG] 第一個 segment: {result.get('segments', [])[0]}")
        return {
            "srt": result.get("srt", ""),
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
        }
