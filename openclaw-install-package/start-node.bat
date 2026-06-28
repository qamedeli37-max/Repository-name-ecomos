@echo off
chcp 65001 > nul
title OpenClaw — Node.js 服务
color 0A

echo ============================================
echo   🚀 OpenClaw — Node.js 服务启动中...
echo ============================================
echo.

:: 检查 .env
if not exist .env (
    echo [!] .env 文件不存在！
    echo     请先运行 install.ps1 完成安装配置
    pause
    exit /b 1
)

:: 检查依赖
if not exist node_modules (
    echo [*] 检测到依赖未安装，正在安装...
    npm install --silent
    if %errorlevel% neq 0 (
        echo [×] 依赖安装失败，请手动执行: npm install
        pause
        exit /b 1
    )
    echo [✓] 依赖安装完成
)

echo [✓] 环境检查通过
echo.
echo   服务地址: http://localhost:3000
echo   按下 Ctrl+C 停止
echo.

node core/index.js

pause
