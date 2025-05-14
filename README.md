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
- **Python 3.10/3.11**（建議 Apple Silicon/arm64 架構）
- **ffmpeg**（需安裝於系統）
- **whispercpp==0.0.17**（需手動下載模型）
- **langdetect**（語言偵測，選用）

## 依賴安裝

```sh
pip install -r requirements.txt
```

## Whisper.cpp CLI 行為說明
- **所有音檔都會自動用 ffmpeg 轉成 16kHz 單聲道 PCM wav**，確保 whisper.cpp CLI 可正確辨識。
- **自動語言偵測**：若未指定語言，會嘗試偵測語言，若非英文自動加上 `--translate` 參數，讓 CLI 強制翻譯成英文。
- **若語音內容為中英文夾雜或口音重，可能出現 (Speaking Chinese) 或 (speaking in foreign language)**：這是 whisper.cpp CLI 的已知現象，與模型大小、音質、語者口音有關。
- **有時可直接顯示中文，有時會被標註為 foreign language**，屬於模型本身的限制。
- **建議使用 large/full 模型提升辨識率**。

## 目前行為整理
- 支援上傳 WAV/MP3/MP4/M4A，最大 500MB。
- 伺服器自動轉檔，無論前端上傳什麼格式都能正確處理。
- 若語音非英文，預設自動翻譯成英文（除非明確指定語言為 zh）。
- 若模型或音檔品質不佳，仍可能出現 (Speaking Chinese) 或 (speaking in foreign language)。
- 產生 SRT 字幕與純文字。

## requirements.txt 範例

```
fastapi==0.115.12
uvicorn==0.34.2
python-multipart==0.0.20
whispercpp==0.0.17
ffmpeg-python==0.2.0
soundfile
pydantic==2.11.4
starlette==0.46.2
pytest==8.3.5
pytest-cov==6.1.1
numpy
langdetect
```

## Whisper 模型下載
- 建議下載 `ggml-medium.bin` 或 `ggml-large-v3.bin`
- 放到 `~/.local/share/whispercpp/ggml-medium.bin`
- [官方下載連結](https://huggingface.co/datasets/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin)

## 啟動 FastAPI 伺服器

```sh
uvicorn src.api.main:app --reload
```

## 其他注意事項
- **隱私優先**：所有音訊與模型皆在本地處理，無任何雲端 API。
- **API 路徑**：`/api/transcribe`，POST 上傳音訊檔案。
- **前端下載時可自選儲存路徑**。

---
如需更多細節，請參考原始碼內的註解。
