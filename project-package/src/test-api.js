/**
 * DeepSeek API 调用测试脚本 (Node.js)
 * =======================================
 * 直接运行：node src/test-api.js
 * 自动读取 .env 中的 DEEPSEEK_API_KEY
 */

require("dotenv").config({ path: require("path").resolve(__dirname, "..", ".env") });

const { DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_API_KEY } = process.env;
const DEEPSEEK_API_URL = `${DEEPSEEK_BASE_URL}/v1/chat/completions`;

async function testDeepSeekAPI() {
  // 1. 校验环境变量
  if (!DEEPSEEK_API_KEY) {
    console.error("❌ DEEPSEEK_API_KEY 未设置！");
    console.error("   请复制 .env.example 为 .env，并填入 API Key");
    process.exit(1);
  }

  if (DEEPSEEK_API_KEY === "sk-your-api-key-here") {
    console.error("❌ DEEPSEEK_API_KEY 仍为默认占位值！");
    console.error("   请在 .env 中填入真实的 API Key");
    process.exit(1);
  }

  console.log("🌐 DeepSeek API 连接测试");
  console.log("━━━━━━━━━━━━━━━━━━━━━━━━");
  console.log(`  地址: ${DEEPSEEK_BASE_URL}`);
  console.log(`  模型: ${DEEPSEEK_MODEL}`);
  console.log(`  密钥: ${DEEPSEEK_API_KEY.substring(0, 8)}...`);
  console.log("");

  // 2. 发送测试请求
  const payload = {
    model: DEEPSEEK_MODEL,
    messages: [
      { role: "system", content: "你是一个有帮助的AI助手。" },
      { role: "user", content: "你好，请用一句话证明你在线。" },
    ],
    max_tokens: 128,
    temperature: 0.7,
  };

  try {
    const resp = await fetch(DEEPSEEK_API_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${DEEPSEEK_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${errText}`);
    }

    const data = await resp.json();
    const reply = data.choices[0].message.content;
    const usage = data.usage;

    console.log("✅ API 调用成功！");
    console.log(`🤖 回复: ${reply}`);
    console.log(`📊 Token: ${JSON.stringify(usage)}`);
  } catch (err) {
    console.error("❌ API 调用失败:", err.message);
    process.exit(1);
  }
}

testDeepSeekAPI();
