# ============================================================
# Dockerfile — OpenClaw 双环境构建
# ============================================================

FROM python:3.12-slim AS python

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env.example .env
COPY core/ ./core/

EXPOSE 8000

CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM node:22-alpine AS node

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --only=production

COPY .env.example .env
COPY core/ ./core/

EXPOSE 3000

CMD ["node", "core/index.js"]
