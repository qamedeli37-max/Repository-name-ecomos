#!/usr/bin/env bash
# ============================================
# OpenClaw — Python 服务启动脚本 (Linux/macOS)
# ============================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🚀 OpenClaw — Python 服务启动中...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 检测 Python
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo -e "${RED}❌ 未检测到 Python${NC}"
    exit 1
fi

# 检查 .env
if [ ! -f ".env" ]; then
    echo -e "${RED}[!] .env 文件不存在！${NC}"
    echo "     请先运行 ./install.sh 完成安装配置"
    exit 1
fi

# 检查依赖
$PY -c "import fastapi" 2>/dev/null || {
    echo -e "${YELLOW}[*] 检测到依赖未安装，正在安装...${NC}"
    $PY -m pip install -r requirements.txt -q
    echo -e "${GREEN}      ✅ 依赖安装完成${NC}"
}

echo -e "${GREEN}      ✅ 环境检查通过${NC}"
echo ""
echo "  服务地址: http://localhost:8000"
echo "  API文档:  http://localhost:8000/docs"
echo "  按下 Ctrl+C 停止"
echo ""

$PY -m uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload
