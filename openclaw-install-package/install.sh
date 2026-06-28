#!/usr/bin/env bash
# ============================================
# OpenClaw 一键安装脚本 (Linux / macOS)
# ============================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  OpenClaw 一键安装脚本 (Linux/macOS)${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ---- 1. 检测 Python ----
echo -e "${YELLOW}[1/7] 检测 Python 环境...${NC}"
if command -v python3 &>/dev/null; then
    PY=python3
elif command -v python &>/dev/null; then
    PY=python
else
    echo -e "${RED}      ❌ 未检测到 Python${NC}"
    echo "      请安装 Python 3.10+"
    echo "      macOS: brew install python@3.12"
    echo "      Ubuntu: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo -e "${GREEN}      ✅ $($PY --version)${NC}"

# ---- 2. 检测 Node.js ----
echo -e "${YELLOW}[2/7] 检测 Node.js 环境...${NC}"
if ! command -v node &>/dev/null; then
    echo -e "${RED}      ❌ 未检测到 Node.js${NC}"
    echo "      请安装 Node.js 18+"
    echo "      macOS: brew install node"
    echo "      Ubuntu: curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash - && sudo apt install -y nodejs"
    exit 1
fi
echo -e "${GREEN}      ✅ Node.js $(node --version)${NC}"

# ---- 3. 创建 .env ----
echo -e "${YELLOW}[3/7] 检查 .env 配置文件...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}      ✅ .env 已从 .env.example 创建${NC}"
        echo -e "${YELLOW}      ⚠ 请编辑 .env 文件，填入你的 DEEPSEEK_API_KEY${NC}"
        echo "        执行: nano .env  或  vim .env"
        echo "        将 your_api_key_here 替换为真实密钥"
        read -p "      编辑完成后按 Enter 继续..."
    else
        echo -e "${RED}      ❌ .env.example 不存在${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}      ✅ .env 已存在${NC}"
fi

# ---- 4. 校验 API Key ----
echo -e "${YELLOW}[4/7] 校验 API Key...${NC}"
if grep -q "your_api_key_here" .env 2>/dev/null; then
    echo -e "${YELLOW}      ⚠ DEEPSEEK_API_KEY 仍为默认占位值${NC}"
    echo "      请编辑 .env 文件，填入真实 API Key"
    read -p "      编辑完成后按 Enter 继续..."
else
    echo -e "${GREEN}      ✅ API Key 已配置${NC}"
fi

# ---- 5. 安装 Python 依赖 ----
echo -e "${YELLOW}[5/7] 安装 Python 依赖...${NC}"
$PY -m pip install --upgrade pip -q 2>/dev/null
$PY -m pip install -r requirements.txt -q
echo -e "${GREEN}      ✅ Python 依赖安装完成${NC}"

# ---- 6. 安装 Node.js 依赖 ----
echo -e "${YELLOW}[6/7] 安装 Node.js 依赖...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}      ✅ node_modules 已存在，跳过${NC}"
else
    npm install --silent 2>/dev/null
    echo -e "${GREEN}      ✅ Node.js 依赖安装完成${NC}"
fi

# ---- 7. 完成 ----
echo -e "${YELLOW}[7/7] OpenClaw 安装完成！${NC}"
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  🚀 OpenClaw 安装完成！${NC}"
echo ""
echo -e "  Python 服务: http://localhost:8000"
echo -e "  API 文档:   http://localhost:8000/docs"
echo -e "  Node 服务:  http://localhost:3000"
echo ""
echo -e "  启动方式:"
echo -e "  • ./start.sh       → 启动 Python 服务"
echo -e "  • ./start-node.sh  → 启动 Node.js 服务"
echo -e "${CYAN}============================================${NC}"
echo ""

read -p "是否现在启动 Python 服务？(Y/n，默认 Y): " choice
if [ "$choice" = "" ] || [ "$choice" = "Y" ] || [ "$choice" = "y" ]; then
    bash start.sh
else
    echo -e "${GREEN}安装完成，随时可以运行 ./start.sh 启动服务。${NC}"
fi
