"""
OpenClaw 核心服务入口
=====================
DeepSeek API 驱动的 AI Agent 服务。
支持 Python FastAPI 模式 和 Node.js 模式（通过 core/index.js）。
"""

import os
import sys
import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, Timeout

# ---------- 加载 .env ----------
load_dotenv()

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
PORT = int(os.getenv("PORT", 8000))

if not DEEPSEEK_API_KEY:
    print("❌ DEEPSEEK_API_KEY 未设置！请复制 .env.example 为 .env 并填入 API Key")
    sys.exit(1)

# ---------- 加载 agent 配置 ----------
AGENT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "agent_config.json")
WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "workflow.json")

def load_json(path: str, label: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 加载 {label} 失败: {e}")
        return {}

agent_config = load_json(AGENT_CONFIG_PATH, "agent_config.json")
workflow = load_json(WORKFLOW_PATH, "workflow.json")

# ---------- 日志 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "logs", "openclaw.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger("openclaw")

# ---------- FastAPI ----------
app = FastAPI(
    title="OpenClaw AI Agent",
    description="DeepSeek API 驱动的 AI Agent 服务 — 解压即用，一键启动",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- API ----------
@app.get("/")
def root():
    return {
        "service": "OpenClaw AI Agent",
        "status": "running",
        "agent": agent_config.get("name", "openclaw-agent"),
        "model": DEEPSEEK_MODEL,
        "endpoints": {
            "chat": "/chat (POST)",
            "health": "/health (GET)",
            "config": "/config (GET)",
            "docs": "/docs",
        },
    }

@app.get("/health")
def health():
    return {"status": "ok", "model": DEEPSEEK_MODEL}

@app.get("/config")
def get_config():
    return {
        "agent": agent_config,
        "workflow": workflow,
        "deepseek": {
            "base_url": DEEPSEEK_BASE_URL,
            "model": DEEPSEEK_MODEL,
        },
    }

@app.post("/chat")
async def chat(prompt: dict):
    user_input = prompt.get("prompt", "")
    if not user_input:
        raise HTTPException(status_code=400, detail="prompt 不能为空")

    logger.info(f"📨 Chat: {user_input[:60]}...")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    system_msg = agent_config.get("system_prompt", "你是一个有帮助的AI助手。")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_input},
        ],
        "max_tokens": prompt.get("max_tokens", 4096),
        "temperature": prompt.get("temperature", 0.7),
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
            logger.info(f"✅ 响应成功")
            return {"reply": reply, "model": DEEPSEEK_MODEL, "usage": data.get("usage")}
        except Exception as e:
            logger.error(f"❌ 调用失败: {e}")
            raise HTTPException(status_code=502, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.main:app", host="0.0.0.0", port=PORT, reload=True)
