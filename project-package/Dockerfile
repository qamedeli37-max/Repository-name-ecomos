# ============================================================
# Dockerfile — 支持 Python 和 Node.js 双环境构建
# ============================================================

# ---- Python 构建阶段 ----
FROM python:3.12-slim AS python

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY .env.example .env
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]


# ---- Node.js 构建阶段 ----
FROM node:22-alpine AS node

WORKDIR /app

# 安装 Node.js 依赖
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# 复制源码
COPY .env.example .env
COPY src/ ./src/

EXPOSE 3000

CMD ["node", "src/index.js"]
