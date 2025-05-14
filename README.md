# Whisper 本地語音轉文字服務

## 專案架構

```
whisper/
├── src/
│   ├── api/
│   │   ├── main.py                # FastAPI 入口，註冊路由與 CORS
│   │   └── transcribe_api.py      # 音訊上傳與轉錄 API 路由
│   ├── transcribe/
│   │   └── whisper_runner.py      # Whisper.cpp 封裝，音訊預處理與轉錄
│   └── utils/                     # 工具函式（可擴充）
├── requirements.txt               # Python 依賴
├── README.md                      # 專案說明
└── frontend/                      # React 前端（如有）
```

## 環境需求
- **Python 3.11**（建議 Apple Silicon/arm64 架構）
- **ffmpeg**（需安裝於系統）
- **whispercpp==0.0.13**（需手動下載模型）

## 推薦安裝流程（Python 3.10 + venv）

1. 安裝 pyenv（如尚未安裝）
   ```sh
   brew install pyenv
   ```
2. 安裝 Python 3.10（建議 3.10.14）
   ```sh
   pyenv install 3.10.14
   ```
3. 建立並啟用專案虛擬環境
   ```sh
   pyenv local 3.10.14
   python3 -m venv venv
   source venv/bin/activate
   ```
4. 升級 pip 並安裝依賴
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. 確認 ffmpeg 已安裝（macOS）
   ```sh
   brew install ffmpeg
   ```

> **注意：**
> - 若遇到 torch、tiktoken 等依賴安裝問題，請務必使用 Python 3.10。
> - Apple Silicon/arm64 用戶建議全程用 pyenv 管理 Python 版本。
> - whispercpp 0.0.17 需手動下載 ggml-medium.bin 至 ~/.local/share/whispercpp/。

## 安裝步驟

1. **安裝 Python 3.11（建議用 pyenv）**
2. **建立虛擬環境並啟用**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```
3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```
4. **手動下載 Whisper 模型**
   - 下載 `ggml-medium.bin`（建議 medium 版）
   - 放到 `~/.local/share/whispercpp/ggml-medium.bin`
   - 下載網址：https://huggingface.co/datasets/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
   ```bash
   mkdir -p ~/.local/share/whispercpp
   cp /下載路徑/ggml-medium.bin ~/.local/share/whispercpp/ggml-medium.bin
   ```
5. **啟動 FastAPI 伺服器**
   ```bash
   uvicorn src.api.main:app --reload
   ```
   > 預設監聽 http://127.0.0.1:8000
6. **前端啟動（如有）**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 注意事項
- **隱私優先**：所有音訊與模型皆在本地處理，無任何雲端 API。
- **模型必須手動下載**，否則會出現 401 Unauthorized 錯誤。
- **支援格式**：WAV、MP3、MP4、M4A，最大 500MB。
- **API 路徑**：`/api/transcribe`，POST 上傳音訊檔案。

## 主要程式註解

### src/api/main.py
```python
"""FastAPI entrypoint for Whisper-like voice-to-text app."""
from fastapi import FastAPI  # 匯入 FastAPI 主框架
from fastapi.middleware.cors import CORSMiddleware  # 匯入 CORS 中介層
from src.api import transcribe_api  # 匯入自訂的 API 路由

app = FastAPI()  # 建立 FastAPI 應用

# CORS for frontend
app.add_middleware(
    CORSMiddleware,  # 加入 CORS 中介層
    allow_origins=["*"],  # 允許所有來源
    allow_credentials=True,  # 允許帶憑證
    allow_methods=["*"],  # 允許所有 HTTP 方法
    allow_headers=["*"],  # 允許所有標頭
)

app.include_router(transcribe_api.router, prefix="/api")  # 註冊 transcribe API 路由

@app.get("/")
def root():  # 健康檢查端點
    """Health check endpoint."""
    return {"status": "success", "data": "Whisper API is running."}  # 回傳服務狀態
```

### src/api/transcribe_api.py
```python
"""FastAPI router for audio upload and transcription."""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks  # 匯入 FastAPI 相關模組
from fastapi.responses import JSONResponse  # 匯入 JSON 回應
from typing import Optional  # 匯入型別註解
import os  # 匯入 os 操作
import shutil  # 匯入檔案操作
from src.transcribe.whisper_runner import WhisperTranscriber  # 匯入轉錄邏輯

router = APIRouter()  # 建立 API 路由

UPLOAD_DIR = "uploads"  # 上傳目錄
os.makedirs(UPLOAD_DIR, exist_ok=True)  # 若不存在則建立

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),  # 上傳檔案
    language: Optional[str] = None,  # 可選語言參數
    background_tasks: BackgroundTasks = None,  # 背景任務
):
    """Handle audio/video file upload and transcription."""
    if file.content_type not in [  # 檢查檔案格式
        "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "video/mp4", "audio/mp4", "audio/x-m4a", "audio/m4a"
    ]:
        return JSONResponse(status_code=400, content={"status": "error", "message": "不支援的音訊/影片格式"})  # 格式錯誤
    if file.size and file.size > 500 * 1024 * 1024:  # 檢查檔案大小
        return JSONResponse(status_code=400, content={"status": "error", "message": "檔案超過 500MB 限制"})

    temp_path = os.path.join(UPLOAD_DIR, file.filename)  # 暫存路徑
    with open(temp_path, "wb") as buffer:  # 寫入檔案
        shutil.copyfileobj(file.file, buffer)

    transcriber = WhisperTranscriber()  # 初始化 Whisper 轉錄器
    wav_path = temp_path + ".wav"  # 預處理後的 wav 路徑
    transcriber.preprocess_audio(temp_path, wav_path)  # 音訊預處理（轉為 16kHz mono wav）
    result = transcriber.transcribe(wav_path, lang=language)  # 進行轉錄

    # 清理暫存
    background_tasks.add_task(os.remove, temp_path)  # 刪除原始檔
    background_tasks.add_task(os.remove, wav_path)  # 刪除轉檔

    return {"status": "success", "data": result}  # 回傳結果
```

### src/transcribe/whisper_runner.py
```python
"""Whisper.cpp Python binding wrapper for local transcription."""
from typing import Optional, Dict, Any  # 型別註解
import os  # 作業系統操作
import ffmpeg  # 音訊轉檔
from whispercpp import Whisper  # Whisper.cpp 綁定

MODEL_PATH = os.getenv("WHISPER_MODEL_PATH", "medium")  # 讀取模型路徑環境變數

class WhisperTranscriber:
    def __init__(self, model_path: str = MODEL_PATH):  # 初始化
        self.model_path = model_path  # 設定模型路徑
        self.whisper = Whisper.from_pretrained(model_path)  # 載入本地模型

    def preprocess_audio(self, input_path: str, output_path: str) -> str:
        """Convert audio to 16kHz mono wav for whisper.cpp."""
        (
            ffmpeg.input(input_path)  # 輸入檔案
            .output(output_path, ar=16000, ac=1, format="wav")  # 轉為 16kHz 單聲道 wav
            .overwrite_output()  # 覆蓋輸出
            .run(quiet=True)  # 靜默執行
        )
        return output_path  # 回傳輸出路徑

    def transcribe(self, audio_path: str, lang: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using whisper.cpp."""
        result = self.whisper.transcribe(audio_path, language=lang, output_format="srt")  # 執行轉錄
        return {
            "srt": result["srt"],  # SRT 字幕
            "text": result["text"],  # 純文字
            "segments": result["segments"],  # 分段資訊
        }
```

---
如需更多細節，請參考原始碼內的註解。
