#!/usr/bin/env bash
# ============================================
# OpenClaw — Node.js 服务启动脚本 (Linux/macOS)
# ============================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🚀 OpenClaw — Node.js 服务启动中...${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 检查 Node.js
if ! command -v node &>/dev/null; then
    echo -e "${RED}❌ 未检测到 Node.js${NC}"
    exit 1
fi

# 检查 .env
if [ ! -f ".env" ]; then
    echo -e "${RED}[!] .env 文件不存在！${NC}"
    echo "     请先运行 ./install.sh 完成安装配置"
    exit 1
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[*] 检测到依赖未安装，正在安装...${NC}"
    npm install --silent 2>/dev/null
    echo -e "${GREEN}      ✅ 依赖安装完成${NC}"
fi

echo -e "${GREEN}      ✅ 环境检查通过${NC}"
echo ""
echo "  服务地址: http://localhost:3000"
echo "  按下 Ctrl+C 停止"
echo ""

node core/index.js
