"""
FastAPI entrypoint for Whisper-like voice-to-text app.
"""
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
