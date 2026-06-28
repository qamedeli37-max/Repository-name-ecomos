@echo off
chcp 65001 > nul
title OpenClaw 项目启动器 — DeepSeek API 集成
color 0A

echo ============================================
echo   OpenClaw 项目 — DeepSeek API 集成
echo   自动安装依赖 + 启动脚本 (Windows)
echo ============================================
echo.

:: 检查 Python
echo [1/6] 检查 Python 环境...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Python，请安装 Python 3.10+
    echo     下载地址：https://www.python.org/downloads/
    echo     安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo     Python %PY_VER%  ✓

:: 检查 Node.js
echo [2/6] 检查 Node.js 环境...
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Node.js，请安装 Node.js 18+
    echo     下载地址：https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1" %%i in ('node --version') do set NODE_VER=%%i
echo     Node.js %NODE_VER%  ✓

:: 检查 .env 文件
echo [3/6] 检查环境配置文件...
if not exist .env (
    if exist .env.example (
        copy .env.example .env > nul
        echo     .env 文件已从 .env.example 创建
        echo     ⚠ 请编辑 .env 文件填入你的 DEEPSEEK_API_KEY
    ) else (
        echo [!] 缺失 .env.example 文件，请检查项目完整性
        pause
        exit /b 1
    )
) else (
    echo     .env 文件已存在 ✓
)

:: 安装 Python 依赖
echo [4/6] 安装 Python 依赖...
python -m pip install --upgrade pip -q > nul 2>&1
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [×] Python 依赖安装失败
    echo     请手动执行：pip install -r requirements.txt
    pause
    exit /b 1
)
echo     Python 依赖安装完成 ✓

:: 安装 Node.js 依赖
echo [5/6] 安装 Node.js 依赖...
if exist node_modules (
    echo     node_modules 已存在，跳过安装 ✓
) else (
    npm install --silent > nul 2>&1
    if %errorlevel% neq 0 (
        echo [×] Node.js 依赖安装失败
        echo     请手动执行：npm install
        pause
        exit /b 1
    )
    echo     Node.js 依赖安装完成 ✓
)

:: 启动项目
echo [6/6] 启动项目...
echo.
echo ============================================
echo   🚀 项目启动中...
echo   Python API: http://localhost:8000
echo   Node API:   http://localhost:3000
echo   按下 Ctrl+C 停止
echo ============================================
echo.

:: 默认启动 Python 服务，如需启动 Node 请取消下面一行的注释
:: python src/main.py
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

:: 启动 Node 版本（Python 服务停止后取消注释下方）
:: node src/index.js

pause
