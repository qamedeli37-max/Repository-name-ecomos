"""
DeepSeek API 集成示例 — Python FastAPI 服务
=============================================
使用环境变量加载 API Key，不硬编码任何密钥。
启动后访问 http://localhost:8000/docs 查看 Swagger 文档
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, Timeout
from loguru import logger
from pydantic import BaseModel, Field

# ---------- 加载 .env 环境变量 ----------
load_dotenv()

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 环境变量检查——启动时硬校验，不等到调用时再报错
if not DEEPSEEK_API_KEY:
    logger.error(
        "❌ DEEPSEEK_API_KEY 未设置！\n"
        "请将 .env.example 复制为 .env，并填入你的 API Key"
    )
    sys.exit(1)

if DEEPSEEK_API_KEY == "sk-your-api-key-here":
    logger.error(
        "❌ DEEPSEEK_API_KEY 仍为占位值！\n"
        "请编辑 .env 文件，将 DEEPSEEK_API_KEY 替换为真实密钥"
    )
    sys.exit(1)

# ---------- 日志配置 ----------
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level:^8}</level> | {message}", colorize=True)
logger.add("logs/app.log", rotation="10 MB", retention=7, level="INFO")

# ---------- 初始化 FastAPI ----------
app = FastAPI(
    title="DeepSeek API 集成服务",
    description="使用环境变量方式调用 DeepSeek API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 数据模型 ----------
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="用户输入的提示词")
    max_tokens: int = Field(default=4096, ge=1, le=8192, description="最大 Token 数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")


class ChatResponse(BaseModel):
    reply: str
    model: str
    usage: dict | None = None


# ---------- API 路由 ----------
@app.get("/")
def root():
    """健康检查"""
    return {
        "status": "running",
        "service": "DeepSeek API Integration",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok", "model": DEEPSEEK_MODEL}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    调用 DeepSeek Chat API

    使用环境变量 DEEPSEEK_API_KEY 进行鉴权，
    Base URL: https://api.deepseek.com
    Model: deepseek-chat
    """
    logger.info(f"📨 收到请求: prompt={request.prompt[:50]}...")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": request.prompt},
        ],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }

    async with AsyncClient(timeout=Timeout(60.0)) as client:
        try:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            reply = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            logger.info(f"✅ 响应成功 | Token 使用: {usage}")

            return ChatResponse(
                reply=reply,
                model=DEEPSEEK_MODEL,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"❌ API 调用失败: {e}")
            raise HTTPException(status_code=502, detail=str(e))


# ---------- 直接运行 ----------
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
