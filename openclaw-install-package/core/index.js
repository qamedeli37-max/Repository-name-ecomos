/**
 * OpenClaw Node.js 核心服务入口
 * =============================
 * 与 Python 版功能对等，使用 Express + OpenAI SDK 调用 DeepSeek API
 */
"use strict";

require("dotenv").config({ path: require("path").resolve(__dirname, "..", ".env") });

const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const OpenAI = require("openai");

// ---- 环境变量 ----
const {
  DEEPSEEK_BASE_URL = "https://api.deepseek.com",
  DEEPSEEK_MODEL = "deepseek-chat",
  DEEPSEEK_API_KEY,
  PORT = 3000,
} = process.env;

if (!DEEPSEEK_API_KEY) {
  console.error("❌ DEEPSEEK_API_KEY 未设置！请复制 .env.example 为 .env 并填入 API Key");
  process.exit(1);
}

// ---- 加载配置 ----
const configPath = path.join(__dirname, "agent_config.json");
const workflowPath = path.join(__dirname, "workflow.json");

function loadJSON(p, label) {
  try { return JSON.parse(fs.readFileSync(p, "utf-8")); }
  catch { console.warn(`⚠️ 加载 ${label} 失败`); return {}; }
}

const agentConfig = loadJSON(configPath, "agent_config.json");
const workflow = loadJSON(workflowPath, "workflow.json");

// ---- 日志 ----
const logFile = path.join(__dirname, "..", "logs", "openclaw.log");
const log = (level, msg) => {
  const ts = new Date().toISOString().replace("T", " ").split(".")[0];
  const line = `${ts} | ${level.padEnd(8)} | ${msg}`;
  console.log(line);
  fs.appendFileSync(logFile, line + "\n", "utf-8");
};

// ---- OpenAI 客户端（兼容 DeepSeek）----
const client = new OpenAI({
  baseURL: DEEPSEEK_BASE_URL,
  apiKey: DEEPSEEK_API_KEY,
  timeout: 60 * 1000,
});

// ---- Express ----
const app = express();
app.use(cors());
app.use(express.json());

app.use((req, _, next) => {
  log("📨", `${req.method} ${req.path}`);
  next();
});

app.get("/", (_, res) => {
  res.json({
    service: "OpenClaw AI Agent (Node.js)",
    status: "running",
    agent: agentConfig.name || "openclaw-agent",
    model: DEEPSEEK_MODEL,
    endpoints: { chat: "POST /chat", health: "GET /health", config: "GET /config" },
  });
});

app.get("/health", (_, res) => res.json({ status: "ok", model: DEEPSEEK_MODEL }));

app.get("/config", (_, res) => res.json({ agent: agentConfig, workflow }));

app.post("/chat", async (req, res) => {
  const { prompt, max_tokens = 4096, temperature = 0.7 } = req.body;
  if (!prompt || !prompt.trim()) return res.status(400).json({ error: "prompt 不能为空" });

  log("📨", `Chat: ${prompt.substring(0, 60)}...`);

  try {
    const completion = await client.chat.completions.create({
      model: DEEPSEEK_MODEL,
      messages: [
        { role: "system", content: agentConfig.system_prompt || "你是一个有帮助的AI助手。" },
        { role: "user", content: prompt },
      ],
      max_tokens: Number(max_tokens),
      temperature: Number(temperature),
    });

    const reply = completion.choices[0].message.content;
    log("✅", "响应成功");
    res.json({ reply, model: DEEPSEEK_MODEL, usage: completion.usage });
  } catch (err) {
    log("❌", `调用失败: ${err.message}`);
    res.status(502).json({ error: "DeepSeek API 调用失败", detail: err.message });
  }
});

app.listen(PORT, () => {
  console.log("");
  log("🚀", `OpenClaw Node.js 服务已启动: http://localhost:${PORT}`);
  log("📘", `API 文档: http://localhost:${PORT}/`);
  log("🤖", `模型: ${DEEPSEEK_MODEL}`);
  console.log("");
});
