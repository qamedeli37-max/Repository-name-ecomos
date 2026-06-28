# 🤖 DeepSeek API 集成项目

> 开箱即用的 DeepSeek API 集成模板，支持 **Python (FastAPI)** 和 **Node.js (Express)** 双端运行。
> 所有密钥均通过环境变量加载，**零硬编码**，安全可靠。

---

## 📋 项目说明

本项目提供完整的 DeepSeek API 集成方案，包含：

- ✅ Python FastAPI Web 服务（含 Swagger 文档）
- ✅ Node.js Express Web 服务
- ✅ 轻量级 Python 命令行客户端
- ✅ 一键启动脚本（Windows / Linux / macOS）
- ✅ Docker Compose 容器化部署
- ✅ 统一的 .env 环境配置
- ✅ 完整的日志记录

### 技术栈

| 语言/工具 | 版本要求 | 用途 |
|-----------|---------|------|
| Python | ≥ 3.10 | FastAPI 后端服务 |
| Node.js | ≥ 18 | Express 后端服务 |
| Docker | ≥ 24.0 | 容器化部署（可选） |
| Docker Compose | ≥ 2.20 | 多容器编排（可选） |

---

## 📁 项目结构

```
project-package/
├── README.md                 # 本文件
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖清单
├── package.json              # Node.js 依赖清单
├── Dockerfile                # Docker 镜像构建文件
├── docker-compose.yml        # Docker 编排文件
├── start.bat                 # Windows 一键启动
├── start.sh                  # Linux/macOS 一键启动
└── src/
    ├── main.py               # Python FastAPI 服务入口
    ├── deepseek_client.py    # Python 轻量客户端示例
    ├── index.js              # Node.js Express 服务入口
    └── test-api.js           # Node.js API 测试脚本
```

---

## 🔧 安装步骤

### 方式一：本地运行（推荐新手）

#### 1. 安装运行环境

**Python 环境（必须 ≥ 3.10）**

- Windows: 从 [python.org](https://www.python.org/downloads/) 下载安装
  - **安装时务必勾选 "Add Python to PATH"**
- macOS: `brew install python@3.12`
- Linux (Ubuntu/Debian): `sudo apt install python3 python3-pip python3-venv`

验证安装：
```bash
python --version
# 输出示例: Python 3.12.4
```

**Node.js 环境（必须 ≥ 18）**

- 从 [nodejs.org](https://nodejs.org/) 下载 LTS 版本安装

验证安装：
```bash
node --version
# 输出示例: v22.12.0
```

#### 2. 下载项目

```bash
# 克隆或下载本项目到本地
git clone <项目地址>
cd project-package
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
# Windows:
copy .env.example .env

# Linux/macOS:
cp .env.example .env
```

#### 4. 填入 API Key

用文本编辑器打开 `.env` 文件，找到这一行：

```ini
DEEPSEEK_API_KEY=sk-your-api-key-here
```

将其替换为你在 [platform.deepseek.com](https://platform.deepseek.com) 获取的真实 API Key：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **重要：** API Key 以 `sk-` 开头，请妥善保管，不要提交到 Git 或分享给他人。

#### 5. 启动项目

**Windows：**
```bash
# 双击 start.bat，或在命令行执行：
start.bat
```

**Linux/macOS：**
```bash
# 给启动脚本添加执行权限（仅首次需要）
chmod +x start.sh

# 运行
./start.sh
```

启动脚本将自动完成：
1. ✅ 检查 Python 和 Node.js 环境
2. ✅ 从 .env.example 创建 .env（如不存在）
3. ✅ 安装所有 Python 依赖（pip install -r requirements.txt）
4. ✅ 安装所有 Node.js 依赖（npm install）
5. 🚀 启动 FastAPI 服务

服务启动后访问：
- **Python API 文档：** http://localhost:8000/docs
- **健康检查：** http://localhost:8000/health

---

### 方式二：Docker 部署（适合服务器）

#### 1. 安装 Docker

- [Docker Desktop (Windows/macOS)](https://www.docker.com/products/docker-desktop/)
- Linux: `curl -fsSL https://get.docker.com | sh`

#### 2. 配置 .env

同方式一第 3-4 步。

#### 3. 启动

```bash
# 启动 Python 服务
docker compose up app-python -d

# 或启动 Node.js 服务
docker compose up app-node -d

# 同时启动所有服务
docker compose up -d
```

#### 4. 查看日志

```bash
docker compose logs -f app-python
```

#### 5. 停止

```bash
docker compose down
```

---

## ⚙️ 环境配置方法

所有配置集中在项目根目录的 `.env` 文件中：

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `DEEPSEEK_API_KEY` | ✅ 是 | — | DeepSeek API 密钥，必填项 |
| `DEEPSEEK_BASE_URL` | ❌ 否 | `https://api.deepseek.com` | API 基础地址，通常无需修改 |
| `DEEPSEEK_MODEL` | ❌ 否 | `deepseek-chat` | 模型名称，通常无需修改 |
| `PORT` | ❌ 否 | `8000` | 服务监听端口 |
| `LOG_LEVEL` | ❌ 否 | `INFO` | 日志级别 |
| `REQUEST_TIMEOUT` | ❌ 否 | `60` | 请求超时秒数 |
| `MAX_TOKENS` | ❌ 否 | `4096` | 单次请求最大 Token 数 |
| `TEMPERATURE` | ❌ 否 | `0.7` | 生成温度 (0.0~2.0) |

---

## 🚀 API 配置方法

### DeepSeek API 调用规范

**统一使用以下参数：**

```
Base URL: https://api.deepseek.com
Model:    deepseek-chat
Auth:     Bearer Token (从环境变量 DEEPSEEK_API_KEY 读取)
```

### Python 调用示例

使用 `src/deepseek_client.py`：

```python
from src.deepseek_client import chat

# 一行调用 DeepSeek API
result = chat("你好，请介绍一下自己")

print(result["reply"])

# 返回结构：
# {
#   "reply": "你好！我是 DeepSeek...",
#   "model": "deepseek-chat",
#   "usage": {"prompt_tokens": 20, "completion_tokens": 50, "total_tokens": 70}
# }
```

直接运行测试：
```bash
python src/deepseek_client.py
```

### Node.js 调用示例

使用 `src/test-api.js`：

```javascript
// API 请求体
const payload = {
  model: "deepseek-chat",
  messages: [
    { role: "system", content: "你是一个有帮助的AI助手。" },
    { role: "user", content: "你好" },
  ],
  max_tokens: 4096,
  temperature: 0.7,
};

// 请求头——API Key 从环境变量读取
const headers = {
  "Authorization": `Bearer ${process.env.DEEPSEEK_API_KEY}`,
  "Content-Type": "application/json",
};

const resp = await fetch("https://api.deepseek.com/v1/chat/completions", {
  method: "POST",
  headers,
  body: JSON.stringify(payload),
});
```

直接运行测试：
```bash
node src/test-api.js
```

---

## 🎯 启动方式汇总

| 方式 | 命令 | 适用场景 |
|------|------|---------|
| Windows 一键启动 | `start.bat` 或双击 | Windows 本地开发 |
| Linux/macOS 一键启动 | `./start.sh` | Linux/macOS 本地开发 |
| Python 直接启动 | `uvicorn src.main:app --reload` | 调试 Python 端 |
| Node.js 直接启动 | `node src/index.js` | 调试 Node.js 端 |
| Docker Python | `docker compose up app-python -d` | 生产部署 |
| Docker Node.js | `docker compose up app-node -d` | 生产部署 |

---

## ❓ 常见错误与解决方案

### 1. `python 不是内部或外部命令`

**原因：** Python 未安装或未添加到 PATH

**解决：**
- 重新安装 Python，安装时**务必勾选 "Add Python to PATH"**
- 或手动将 Python 安装目录添加到系统环境变量 PATH 中

### 2. `DEEPSEEK_API_KEY 未设置`

**原因：** 未创建 .env 文件或未填入 API Key

**解决：**
```bash
# 复制模板文件
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS

# 然后编辑 .env 填入真实 API Key
```

### 3. `DEEPSEEK_API_KEY 仍为占位值`

**原因：** .env 文件中的 API Key 还是默认的 `sk-your-api-key-here`

**解决：** 编辑 `.env` 文件，将 `sk-your-api-key-here` 替换为真实 API Key

### 4. `pip 不是内部或外部命令`

**原因：** Python 安装不完整或 PATH 配置有问题

**解决：**
```bash
# 尝试使用 python -m pip
python -m pip install -r requirements.txt
```

### 5. `ModuleNotFoundError: No module named 'xxxx'`

**原因：** Python 依赖未安装

**解决：**
```bash
pip install -r requirements.txt
```

### 6. `npm 不是内部或外部命令`

**原因：** Node.js 未安装

**解决：** 从 [nodejs.org](https://nodejs.org/) 下载安装 LTS 版本

### 7. 启动后浏览器打开报 502

**原因：** DeepSeek API 调用失败，可能原因：
- API Key 无效或已过期
- 网络无法访问 api.deepseek.com
- 请求超时

**解决：**
1. 检查 .env 中的 API Key 是否正确
2. 检查网络连接，确保能访问 api.deepseek.com
3. 查看控制台日志了解具体错误信息

### 8. Docker 启动报 `command not found`

**原因：** 未安装 Docker 或 Docker Compose

**解决：**
- 安装 Docker Desktop
- 或仅使用本地方式运行（方式一），无需 Docker

### 9. Windows 上 `start.bat` 闪退

**原因：** 脚本执行出错

**解决：**
1. 打开 PowerShell 或 CMD
2. 切换到项目目录
3. 手动逐行执行脚本内容，查看具体报错

---

## 📄 许可证

MIT License

## 💬 支持

如有问题，请提交 Issue 或联系项目维护者。
