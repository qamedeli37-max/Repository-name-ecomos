#!/usr/bin/env bash
set -e

# ============================================
# OpenClaw 项目 — DeepSeek API 集成
# 自动安装依赖 + 启动脚本 (Linux / macOS)
# ============================================

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  OpenClaw 项目 — DeepSeek API 集成${NC}"
echo -e "${GREEN}  自动安装依赖 + 启动脚本 (Linux/macOS)${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# ---- 1. 检查 Python ----
echo -e "[1/6] 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo -e "${RED}[!] 未检测到 Python，请安装 Python 3.10+${NC}"
    echo "     https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$($PYTHON --version 2>&1)
echo -e "     ${GREEN}$PY_VER ✓${NC}"

# ---- 2. 检查 Node.js ----
echo -e "[2/6] 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}[!] 未检测到 Node.js，请安装 Node.js 18+${NC}"
    echo "     https://nodejs.org/"
    exit 1
fi
NODE_VER=$(node --version 2>&1)
echo -e "     ${GREEN}Node.js $NODE_VER ✓${NC}"

# ---- 3. 检查 .env ----
echo -e "[3/6] 检查环境配置文件..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "     ${YELLOW}.env 文件已从 .env.example 创建${NC}"
        echo -e "     ${YELLOW}⚠ 请编辑 .env 文件填入你的 DEEPSEEK_API_KEY${NC}"
    else
        echo -e "${RED}[!] 缺失 .env.example 文件${NC}"
        exit 1
    fi
else
    echo -e "     ${GREEN}.env 文件已存在 ✓${NC}"
fi

# ---- 4. 安装 Python 依赖 ----
echo -e "[4/6] 安装 Python 依赖..."
$PYTHON -m pip install --upgrade pip -q 2>/dev/null
$PYTHON -m pip install -r requirements.txt -q
echo -e "     ${GREEN}Python 依赖安装完成 ✓${NC}"

# ---- 5. 安装 Node.js 依赖 ----
echo -e "[5/6] 安装 Node.js 依赖..."
if [ -d "node_modules" ]; then
    echo -e "     ${GREEN}node_modules 已存在，跳过安装 ✓${NC}"
else
    npm install --silent 2>/dev/null
    echo -e "     ${GREEN}Node.js 依赖安装完成 ✓${NC}"
fi

# ---- 6. 启动 ----
echo -e "[6/6] 启动项目..."
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🚀 项目启动中...${NC}"
echo -e "${GREEN}  Python API: http://localhost:8000${NC}"
echo -e "${GREEN}  Node API:   http://localhost:3000${NC}"
echo -e "${GREEN}  按下 Ctrl+C 停止${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 默认启动 Python 服务
$PYTHON -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 如需启动 Node 服务，注释上面这行，取消下面这行的注释
# node src/index.js
