# 🔑 DeepSeek API 配置指南

---

## 一、注册 DeepSeek 账号

1. 打开浏览器访问 [https://platform.deepseek.com](https://platform.deepseek.com)
2. 点击右上角 **"Sign Up"** 注册账号
   - 支持邮箱注册
   - 注册后需要邮箱验证
3. 登录成功后进入控制台

---

## 二、获取 API Key

1. 登录后，在左侧菜单找到 **"API Keys"**
2. 点击 **"Create API Key"**
3. 输入名称（例如 `openclaw-agent`）
4. 点击确认生成
5. **立即复制并保存你的 API Key**（关闭弹窗后将不再显示完整密钥）

> ⚠️ API Key 格式示例：`sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 三、配置到 OpenClaw

### 方法 1：手动编辑 .env 文件

1. 打开项目根目录下的 `.env` 文件
2. 找到这一行：
   ```
   DEEPSEEK_API_KEY=your_api_key_here
   ```
3. 将 `your_api_key_here` 替换为你的真实 API Key：
   ```
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
4. 保存文件

### 方法 2：通过安装脚本自动配置

运行 `install.ps1`（Windows）或 `install.sh`（Linux/Mac），
脚本会：
- 自动从 `.env.example` 创建 `.env`
- 用记事本/vim 打开 `.env` 供你编辑
- 校验 API Key 是否已配置

---

## 四、验证配置

配置完成后，启动服务并测试：

### 方式 A：启动服务后测试

```bash
# 启动 Python 服务
start.bat  # Windows
./start.sh # Linux/macOS
```

打开浏览器访问 `http://localhost:8000/docs`，
在 Swagger 页面中点击 `/chat` → **Try it out**，发送：

```json
{
  "prompt": "你好，请用一句话介绍自己"
}
```

### 方式 B：直接运行测试脚本

Windows：
```powershell
python -c "
import httpx, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('DEEPSEEK_API_KEY')
resp = httpx.post('https://api.deepseek.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={'model':'deepseek-chat','messages':[{'role':'user','content':'你好'}]}, timeout=30)
print(resp.json()['choices'][0]['message']['content'])
"
```

Linux/macOS：
```bash
python3 -c "
import httpx, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('DEEPSEEK_API_KEY')
resp = httpx.post('https://api.deepseek.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={'model':'deepseek-chat','messages':[{'role':'user','content':'你好'}]}, timeout=30)
print(resp.json()['choices'][0]['message']['content'])
"
```

---

## 五、API 调用规范

| 参数 | 值 |
|------|-----|
| Base URL | `https://api.deepseek.com` |
| 模型 | `deepseek-chat` |
| 鉴权方式 | `Authorization: Bearer <你的API Key>` |
| 请求方式 | POST |
| 接口路径 | `/v1/chat/completions` |

### Python 调用示例

```python
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "你是一个有帮助的AI助手。"},
        {"role": "user", "content": "你好"},
    ],
    "max_tokens": 4096,
    "temperature": 0.7,
}

with httpx.Client(timeout=60) as client:
    resp = client.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload)
    data = resp.json()
    print(data["choices"][0]["message"]["content"])
```

### Node.js 调用示例

```javascript
require("dotenv").config();

const apiKey = process.env.DEEPSEEK_API_KEY;
const baseURL = process.env.DEEPSEEK_BASE_URL || "https://api.deepseek.com";
const model = process.env.DEEPSEEK_MODEL || "deepseek-chat";

const payload = {
  model,
  messages: [
    { role: "system", content: "你是一个有帮助的AI助手。" },
    { role: "user", content: "你好" },
  ],
  max_tokens: 4096,
  temperature: 0.7,
};

fetch(`${baseURL}/v1/chat/completions`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify(payload),
})
  .then((r) => r.json())
  .then((data) => console.log(data.choices[0].message.content))
  .catch((err) => console.error("调用失败:", err));
```

---

## 六、注意事项

- 🔒 **API Key 务必保密**，不要上传到 GitHub 或分享给他人
- 💰 DeepSeek API 提供免费额度，具体额度以官网公告为准
- 🌐 如果无法访问 `api.deepseek.com`，请检查网络环境
- ⏱ 超时时间建议设为 60 秒以上
