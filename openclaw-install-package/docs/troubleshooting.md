# 🛠 常见错误与解决方案

---

## 安装阶段

### 1. `python 不是内部或外部命令`

**原因：** Python 未安装或未添加到系统 PATH

**解决方案：**
1. 从 [python.org](https://www.python.org/downloads/) 下载 Python 3.10+
2. 安装时**务必勾选 "Add Python to PATH"**
3. 安装完成后重启终端，再次运行 `python --version` 验证

---

### 2. `pip 不是内部或外部命令`

**原因：** Python 安装未勾选 pip，或 PATH 配置不完整

**解决方案：**
```bash
# 使用 python -m pip 替代 pip
python -m pip install -r requirements.txt
```

---

### 3. `node 不是内部或外部命令`

**原因：** Node.js 未安装

**解决方案：**
1. 从 [nodejs.org](https://nodejs.org/) 下载 LTS 版本
2. 安装时保持默认选项（会自动添加到 PATH）
3. 安装完成后重启终端，运行 `node --version` 验证

---

### 4. `npm 不是内部或外部命令`

**原因：** Node.js 安装时未勾选 npm 组件

**解决方案：**
- 重新安装 Node.js，选择完整安装
- 或使用 [nvm-windows](https://github.com/coreybutler/nvm-windows) 重新安装

---

### 5. pip 安装依赖时报错 `Microsoft Visual C++ 14.0 is required`

**原因：** 部分 Python 包需要 C++ 编译环境

**解决方案：**

**Windows：**
1. 下载 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 安装时勾选 **"C++ build tools"**
3. 重启终端，重新执行 `pip install -r requirements.txt`

**macOS：**
```bash
xcode-select --install
```

**Linux (Ubuntu/Debian)：**
```bash
sudo apt install build-essential
```

---

## 运行阶段

### 6. 启动后报 `DEEPSEEK_API_KEY 未设置`

**原因：** `.env` 文件不存在或未正确配置

**解决方案：**
```bash
# 确保 .env 已创建
# Windows:
copy .env.example .env

# Linux/macOS:
cp .env.example .env
```

然后编辑 `.env`，将 `your_api_key_here` 替换为真实 API Key。

---

### 7. 启动后报 `DEEPSEEK_API_KEY 仍为占位值`

**原因：** `.env` 文件中的 API Key 仍是默认的 `your_api_key_here`

**解决方案：**
1. 用文本编辑器打开 `.env`
2. 找到 `DEEPSEEK_API_KEY=your_api_key_here`
3. 替换为真实 API Key（以 `sk-` 开头）
4. 保存文件，重新启动

---

### 8. 启动后 API 报 502 错误

**原因：** DeepSeek API 调用失败

**可能的原因和解决方案：**

| 原因 | 解决方案 |
|------|---------|
| API Key 无效或过期 | 登录 [platform.deepseek.com](https://platform.deepseek.com) 检查 API Key 状态 |
| 网络无法访问 api.deepseek.com | 检查网络连接，可能需要配置代理 |
| 请求超时 | 检查 `.env` 中的 TIMEOUT 值（建议 ≥ 60） |
| API 服务故障 | 等待几分钟后重试，或查看 [DeepSeek Status](https://status.deepseek.com) |

---

### 9. 端口被占用（`Address already in use`）

**原因：** 8000 端口已被其他程序占用

**解决方案：**

**方案 A：修改端口**
编辑 `.env` 文件，修改 `PORT` 值：
```ini
PORT=8080
```

**方案 B：查找并关闭占用进程**

Windows：
```powershell
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F
```

Linux/macOS：
```bash
lsof -i :8000
kill -9 <进程ID>
```

---

### 10. `uvicorn` 启动报 `ModuleNotFoundError`

**原因：** Python 依赖未安装或安装不完整

**解决方案：**
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 如果还是报错，检查 Python 环境是否为虚拟环境
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import httpx; print('httpx OK')"
```

---

### 11. Docker 部署报错

**原因：** Docker 环境未正确安装或配置

**解决方案：**
```bash
# 验证 Docker 是否安装
docker --version

# 验证 Docker Compose 是否安装
docker compose version

# 如果未安装，请下载 Docker Desktop
# Windows/Mac: https://www.docker.com/products/docker-desktop/
# Linux: curl -fsSL https://get.docker.com | sh

# 构建镜像时如果网络慢，可以尝试国内镜像加速
```

---

## 其他问题

### 12. 中文显示乱码

**原因：** 终端编码问题

**解决方案：**

**Windows PowerShell：**
```powershell
chcp 65001
```

**Windows CMD：**
```cmd
chcp 65001
```

**macOS/Linux 终端通常不需要额外设置。**

---

### 13. `start.sh` 提示 `Permission denied`

**原因：** 脚本没有执行权限

**解决方案：**
```bash
chmod +x start.sh start-node.sh install.sh
```

---

### 14. 使用代理时无法访问 API

**原因：** 代理影响了 httpx/node-fetch 的网络请求

**解决方案：**

**Python（绕过代理）：**
```python
# 在代码中为 httpx 设置代理
client = httpx.Client(proxies={"http://": None, "https://": None}, timeout=60)
```

或设置环境变量临时关闭代理：
```bash
# Linux/macOS
NO_PROXY=api.deepseek.com ./start.sh

# Windows PowerShell
$env:NO_PROXY="api.deepseek.com"; .\start.bat
```

---

### 15. 还有问题？

如果以上解决方案都不能解决，请执行以下命令收集诊断信息：

Windows：
```powershell
python --version
node --version
pip list
type .env
```

Linux/macOS：
```bash
python3 --version
node --version
pip3 list
cat .env
```

并将输出连同错误信息一起提交 Issue。我们会尽快回复。
