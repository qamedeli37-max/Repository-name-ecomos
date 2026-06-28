<#
.SYNOPSIS
  OpenClaw 一键安装脚本 (Windows PowerShell)
.DESCRIPTION
  自动检测环境 → 安装依赖 → 配置 .env → 启动服务
#>

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "OpenClaw 安装程序"
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  OpenClaw 一键安装脚本 (Windows)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ---- 1. 检测 Python ----
Write-Host "[1/7] 检测 Python 环境..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "      ✅ $pyVer" -ForegroundColor Green
} catch {
    Write-Host "      ❌ 未检测到 Python" -ForegroundColor Red
    Write-Host "      请从 https://www.python.org/downloads/ 下载 Python 3.10+"
    Write-Host "      安装时务必勾选 'Add Python to PATH'"
    Read-Host "      安装完成后按 Enter 继续"
}

# ---- 2. 检测 Node.js ----
Write-Host "[2/7] 检测 Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVer = node --version
    Write-Host "      ✅ Node.js $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "      ❌ 未检测到 Node.js" -ForegroundColor Red
    Write-Host "      请从 https://nodejs.org/ 下载安装 Node.js 18+"
    Read-Host "      安装完成后按 Enter 继续"
}

# ---- 3. 创建 .env ----
Write-Host "[3/7] 检查 .env 配置文件..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "      ✅ .env 已从 .env.example 创建" -ForegroundColor Green
        Write-Host "      ⚠ 请编辑 .env 文件，填入你的 DEEPSEEK_API_KEY" -ForegroundColor Yellow
        Write-Host "        用记事本打开 .env，将 your_api_key_here 替换为真实密钥" -ForegroundColor Yellow
        Start-Process notepad.exe (Resolve-Path ".env")
        Read-Host "      编辑完成后按 Enter 继续"
    } else {
        Write-Host "      ❌ .env.example 不存在，请检查安装包完整性" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "      ✅ .env 已存在" -ForegroundColor Green
}

# ---- 4. 校验 API Key ----
Write-Host "[4/7] 校验 API Key..." -ForegroundColor Yellow
$envContent = Get-Content ".env" -Raw
if ($envContent -match "your_api_key_here") {
    Write-Host "      ⚠ DEEPSEEK_API_KEY 仍为默认占位值" -ForegroundColor Yellow
    Write-Host "      请编辑 .env 文件，填入你的真实 API Key" -ForegroundColor Yellow
    Start-Process notepad.exe (Resolve-Path ".env")
    Read-Host "      编辑完成后按 Enter 继续"
} else {
    Write-Host "      ✅ API Key 已配置" -ForegroundColor Green
}

# ---- 5. 安装 Python 依赖 ----
Write-Host "[5/7] 安装 Python 依赖..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q 2>$null
pip install -r requirements.txt -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "      ✅ Python 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "      ❌ Python 依赖安装失败，请手动执行: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

# ---- 6. 安装 Node.js 依赖 ----
Write-Host "[6/7] 安装 Node.js 依赖..." -ForegroundColor Yellow
if (Test-Path "node_modules") {
    Write-Host "      ✅ node_modules 已存在，跳过" -ForegroundColor Green
} else {
    npm install --silent 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✅ Node.js 依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "      ❌ Node.js 依赖安装失败，请手动执行: npm install" -ForegroundColor Red
        exit 1
    }
}

# ---- 7. 启动 ----
Write-Host "[7/7] 启动 OpenClaw 服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  🚀 OpenClaw 安装完成！" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan
Write-Host "  Python 服务: http://localhost:8000" -ForegroundColor White
Write-Host "  API 文档:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Node 服务:  http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "  启动方式:" -ForegroundColor Cyan
Write-Host "  • 双击 start.bat     → 启动 Python 服务" -ForegroundColor White
Write-Host "  • 双击 start-node.bat → 启动 Node.js 服务" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "是否现在启动 Python 服务？(Y/N，默认 Y) " -ForegroundColor Yellow -NoNewline
$choice = Read-Host
if ($choice -eq "" -or $choice -match "^[Yy]") {
    .\start.bat
} else {
    Write-Host "安装完成，随时可以运行 start.bat 启动服务。" -ForegroundColor Green
}
