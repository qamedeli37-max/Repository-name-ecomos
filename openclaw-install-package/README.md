# 🤖 OpenClaw — 一键安装部署包

> **解压即用 · 自动安装 · 一键启动 · 可复制传播**
>
> 基于 DeepSeek API 的 AI Agent 服务，支持 Python (FastAPI) 和 Node.js (Express) 双端运行。

---

## 📖 项目介绍

OpenClaw 是一个开箱即用的 AI Agent 部署包，通过 DeepSeek API 提供智能对话能力。

**核心特性：**

| 特性 | 说明 |
|------|------|
| ✅ 解压即用 | 下载压缩包，解压到任意目录即可开始安装 |
| ✅ 自动依赖安装 | 自动检测 Python/Node.js 环境，自动安装所有依赖 |
| ✅ 双语言支持 | Python FastAPI + Node.js Express 两份完整实现 |
| ✅ DeepSeek API | 统一接入 `deepseek-chat` 模型 |
| ✅ 一键启动 | 双击 `.bat` 或运行 `.sh` 即可启动服务 |
| ✅ Docker 部署 | 支持 `docker compose up -d` 容器化部署 |
| ✅ 完整文档 | 安装、配置、API 调用、排错全覆盖 |

---

## 📁 项目结构

```
openclaw-install-package/
│
├── README.md                  # 本文件 — 项目总说明
├── .env.example               # 环境变量模板（复制为 .env 后填入 API Key）
├── requirements.txt           # Python 依赖清单
├── package.json               # Node.js 依赖清单
├── Dockerfile                 # Docker 镜像构建文件
├── docker-compose.yml         # Docker 编排文件
│
├── install.ps1                # 🪟 Windows 一键安装脚本（推荐首次运行）
├── install.sh                 # 🐧🍎 Linux/macOS 一键安装脚本（推荐首次运行）
├── start.bat                  # 🪟 Windows 启动 Python 服务
├── start-node.bat             # 🪟 Windows 启动 Node.js 服务
├── start.sh                   # 🐧🍎 Linux/macOS 启动 Python 服务
├── start-node.sh              # 🐧🍎 Linux/macOS 启动 Node.js 服务
│
├── core/
│   ├── main.py                # Python FastAPI 服务入口
│   ├── index.js               # Node.js Express 服务入口
│   ├── agent_config.json      # Agent 配置（名称、系统提示词等）
│   └── workflow.json          # 默认工作流定义
│
├── docs/
│   ├── api_setup.md           # DeepSeek API 获取与配置指南
│   └── troubleshooting.md     # 15 种常见错误与解决方案
│
└── logs/                      # 运行日志目录（自动创建）
    └── openclaw.log
```

---

## 📥 安装步骤（面向新手）

### 第一步：准备运行环境

**需要安装以下两个软件：**

#### 1️⃣ 安装 Python（必须 ≥ 3.10）

| 系统 | 安装方式 |
|------|---------|
| **Windows** | 从 [python.org](https://www.python.org/downloads/) 下载安装包 → **安装时务必勾选 ☑ "Add Python to PATH"** |
| **macOS** | `brew install python@3.12` |
| **Ubuntu/Debian** | `sudo apt update && sudo apt install python3 python3-pip python3-venv` |

验证安装（在终端中执行）：
```bash
python --version
# 应输出类似: Python 3.12.4
```

#### 2️⃣ 安装 Node.js（必须 ≥ 18）

| 系统 | 安装方式 |
|------|---------|
| **Windows** | 从 [nodejs.org](https://nodejs.org/) 下载 LTS 版本 → 下一步安装即可 |
| **macOS** | `brew install node` |
| **Ubuntu/Debian** | `curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash - && sudo apt install -y nodejs` |

验证安装：
```bash
node --version
# 应输出类似: v22.12.0
```

---

### 第二步：解压并安装

#### 🪟 Windows 用户

1. 将 `openclaw-install-package.zip` **解压到纯英文路径**（例如 `D:\openclaw`，不要有中文和空格）
2. 进入解压后的文件夹
3. **右键点击 `install.ps1` → "使用 PowerShell 运行"**
4. 安装脚本会：
   - ✅ 检测 Python 和 Node.js 是否已安装
   - ✅ 自动将 `.env.example` 复制为 `.env`
   - ✅ 打开记事本让你填入 API Key
   - ✅ 自动安装所有 Python 依赖
   - ✅ 自动安装所有 Node.js 依赖
   - ✅ 询问是否立即启动服务

#### 🐧🍎 Linux/macOS 用户

```bash
# 1. 解压
unzip openclaw-install-package.zip -d ~/openclaw
cd ~/openclaw

# 2. 添加执行权限（仅首次）
chmod +x install.sh start.sh start-node.sh

# 3. 运行安装脚本
./install.sh
```

---

### 第三步：获取并配置 API Key

1. 访问 [https://platform.deepseek.com](https://platform.deepseek.com)
2. 注册/登录 → 进入控制台
3. 左侧菜单找到 **"API Keys"** → **"Create API Key"**
4. 复制生成的密钥（格式：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

配置方式：

用文本编辑器打开项目根目录的 `.env` 文件，找到：
```ini
DEEPSEEK_API_KEY=your_api_key_here
```
替换为：
```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> 详细指南请参考 [api_setup.md](docs/api_setup.md)

---

## 🚀 启动方式

### 方式一：启动 Python 服务（推荐）

| 系统 | 命令 |
|------|------|
| **Windows** | 双击 `start.bat` |
| **Linux/macOS** | `./start.sh` |

启动后访问：
- **API 服务：** http://localhost:8000
- **Swagger 文档：** http://localhost:8000/docs

### 方式二：启动 Node.js 服务

| 系统 | 命令 |
|------|------|
| **Windows** | 双击 `start-node.bat` |
| **Linux/macOS** | `./start-node.sh` |

启动后访问：
- **API 服务：** http://localhost:3000

### 方式三：Docker 部署

```bash
# 启动 Python 服务（后台）
docker compose up openclaw-python -d

# 启动 Node.js 服务（后台）
docker compose up openclaw-node -d

# 查看日志
docker compose logs -f openclaw-python

# 停止所有服务
docker compose down
```

---

## 🔧 API 配置方法

### DeepSeek API 调用规范

| 参数 | 固定值 |
|------|--------|
| **Base URL** | `https://api.deepseek.com` |
| **Model** | `deepseek-chat` |
| **鉴权** | `Authorization: Bearer <DEEPSEEK_API_KEY>`（从环境变量读取） |
| **请求方式** | POST `/v1/chat/completions` |

### Python 调用示例

```python
import os, httpx
from dotenv import load_dotenv

load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
    "Content-Type": "application/json",
}
payload = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 4096,
}
r = httpx.post("https://api.deepseek.com/v1/chat/completions",
               headers=headers, json=payload, timeout=60)
print(r.json()["choices"][0]["message"]["content"])
```

### Node.js 调用示例

```javascript
require("dotenv").config();
const apiKey = process.env.DEEPSEEK_API_KEY;

fetch("https://api.deepseek.com/v1/chat/completions", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "deepseek-chat",
    messages: [{ role: "user", content: "你好" }],
    max_tokens: 4096,
  }),
})
  .then(r => r.json())
  .then(d => console.log(d.choices[0].message.content));
```

---

## ⚙️ 环境变量说明

所有配置集中在 `.env` 文件中。

| 变量名 | 是否必填 | 默认值 | 说明 |
|--------|---------|--------|------|
| `DEEPSEEK_API_KEY` | ✅ 是 | — | DeepSeek API 密钥（以 `sk-` 开头） |
| `DEEPSEEK_BASE_URL` | ❌ 否 | `https://api.deepseek.com` | API 基础地址，通常无需修改 |
| `DEEPSEEK_MODEL` | ❌ 否 | `deepseek-chat` | 模型名称，通常无需修改 |
| `PORT` | ❌ 否 | `8000` | Python 服务监听端口 |
| `NODE_PORT` | ❌ 否 | `3000` | Node.js 服务监听端口 |
| `LOG_LEVEL` | ❌ 否 | `INFO` | 日志输出级别 |
| `TIMEOUT` | ❌ 否 | `60` | API 请求超时时间（秒） |
| `MAX_TOKENS` | ❌ 否 | `4096` | 单次请求最大 Token 数 |
| `TEMPERATURE` | ❌ 否 | `0.7` | 生成温度（0.0~2.0） |

---

## ❓ 常见问题速览

| 问题 | 原因 | 解决 |
|------|------|------|
| `python 不是内部或外部命令` | Python 未安装或未添加 PATH | 重新安装 Python，勾选 "Add Python to PATH" |
| `DEEPSEEK_API_KEY 未设置` | 未创建 .env 或未填入 | `copy .env.example .env` 后编辑填入 |
| 启动后访问报 502 | API Key 无效或网络不通 | 检查 API Key 和网络连接 |
| 端口被占用 | 8000 端口已被其他程序使用 | 修改 `.env` 中的 `PORT` 值 |
| 中文乱码 | 终端编码问题 | PowerShell 执行 `chcp 65001` |

**遇到其他问题？** 请查看完整的 [troubleshooting.md](docs/troubleshooting.md)，覆盖 15 种常见场景的详细解决方案。

---

## 📦 打包发布说明

> ✅ **此项目可直接压缩为 `openclaw-install-package.zip` 发布使用**

打包方式：

```bash
# 确认项目目录结构完整后
# Windows:
Compress-Archive -Path "openclaw-install-package\*" -DestinationPath "openclaw-install-package.zip"

# Linux/macOS:
zip -r openclaw-install-package.zip openclaw-install-package/
```

接收方操作流程：
1. 解压 zip → 2. 安装 Python 和 Node.js → 3. 双击 `install.ps1` → 4. 填入 API Key → 5. 双击 `start.bat`

全程无需手动安装任何依赖，无需任何命令行操作。

---

## 📄 许可证

MIT License

---

## 💬 支持

- 问题反馈：提交 GitHub Issue
- DeepSeek 官网：https://platform.deepseek.com
- API 状态查询：https://status.deepseek.com

---

*OpenClaw — 让 AI 部署变得简单*
