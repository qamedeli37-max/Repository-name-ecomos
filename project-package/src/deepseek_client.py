"""
DeepSeek API 简洁 Python 客户端
================================
轻量级封装，不依赖 FastAPI/Express，可直接 `python src/deepseek_client.py` 运行。
仅需 .env 文件中的 DEEPSEEK_API_KEY。
"""

import os
from dotenv import load_dotenv
import httpx

load_dotenv()

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def check_env():
    """校验环境变量"""
    if not DEEPSEEK_API_KEY:
        raise ValueError(
            "❌ DEEPSEEK_API_KEY 未设置！\n"
            "请复制 .env.example 为 .env 并填入 API Key"
        )
    if DEEPSEEK_API_KEY == "sk-your-api-key-here":
        raise ValueError(
            "❌ DEEPSEEK_API_KEY 仍为默认占位值！\n"
            "请在 .env 中填入真实的 API Key"
        )


def chat(prompt: str, max_tokens: int = 4096, temperature: float = 0.7) -> dict:
    """
    调用 DeepSeek Chat API

    参数:
        prompt: 用户输入
        max_tokens: 最大 Token 数
        temperature: 温度参数 (0.0 ~ 2.0)

    返回:
        包含 reply, model, usage 的字典
    """
    check_env()

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个有帮助的AI助手。"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    return {
        "reply": data["choices"][0]["message"]["content"],
        "model": data["model"],
        "usage": data.get("usage"),
    }


if __name__ == "__main__":
    # 使用示例：直接运行即可测试
    try:
        result = chat("用一句话介绍 DeepSeek")
        print(f"\n🤖 {result['model']}")
        print(f"💬 {result['reply']}")
        print(f"📊 Token 使用: {result['usage']}")
    except Exception as e:
        print(f"❌ 错误: {e}")
