/**
 * DeepSeek API 集成示例 — Node.js Express 服务
 * ==============================================
 * 使用环境变量加载 API Key，不硬编码任何密钥。
 * 启动后访问 http://localhost:3000
 */

"use strict";

// ---------- 加载 .env 环境变量 ----------
require("dotenv").config();

const express = require("express");
const cors = require("cors");
const OpenAI = require("openai");
const fs = require("fs");
const path = require("path");
const winston = require("winston");

// ---------- 环境变量校验 ----------
const {
  DEEPSEEK_BASE_URL = "https://api.deepseek.com",
  DEEPSEEK_MODEL = "deepseek-chat",
  DEEPSEEK_API_KEY,
  PORT = 3000,
  LOG_LEVEL = "INFO",
} = process.env;

if (!DEEPSEEK_API_KEY) {
  console.error(
    "❌ DEEPSEEK_API_KEY 未设置！\n" +
    "请将 .env.example 复制为 .env，并填入你的 API Key"
  );
  process.exit(1);
}

if (DEEPSEEK_API_KEY === "sk-your-api-key-here") {
  console.error(
    "❌ DEEPSEEK_API_KEY 仍为占位值！\n" +
    "请编辑 .env 文件，将 DEEPSEEK_API_KEY 替换为真实密钥"
  );
  process.exit(1);
}

// ---------- 日志配置 ----------
const logger = winston.createLogger({
  level: LOG_LEVEL.toLowerCase(),
  format: winston.format.combine(
    winston.format.timestamp({ format: "HH:mm:ss" }),
    winston.format.printf(({ timestamp, level, message }) => {
      return `${timestamp} | ${level.toUpperCase().padEnd(8)} | ${message}`;
    })
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({
      filename: path.join(__dirname, "..", "logs", "app.log"),
      maxsize: 10 * 1024 * 1024,
      maxFiles: 7,
    }),
  ],
});

// ---------- 初始化 OpenAI 客户端 (兼容 DeepSeek) ----------
const client = new OpenAI({
  baseURL: DEEPSEEK_BASE_URL,
  apiKey: DEEPSEEK_API_KEY,
  timeout: 60 * 1000,
});

// ---------- 初始化 Express ----------
const app = express();

app.use(cors());
app.use(express.json());

// ---------- 中间件：请求日志 ----------
app.use((req, res, next) => {
  logger.info(`📨 ${req.method} ${req.path}`);
  next();
});

// ---------- 路由 ----------

// 健康检查
app.get("/", (req, res) => {
  res.json({
    status: "running",
    service: "DeepSeek API Integration (Node.js)",
    endpoints: {
      chat: "POST /chat",
      health: "GET /health",
    },
  });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok", model: DEEPSEEK_MODEL });
});

// Chat 接口
app.post("/chat", async (req, res) => {
  const { prompt, max_tokens = 4096, temperature = 0.7 } = req.body;

  if (!prompt || typeof prompt !== "string" || prompt.trim().length === 0) {
    return res.status(400).json({ error: "prompt 字段不能为空" });
  }

  logger.info(`📨 Chat 请求: ${prompt.substring(0, 50)}...`);

  try {
    const completion = await client.chat.completions.create({
      model: DEEPSEEK_MODEL,
      messages: [
        { role: "system", content: "你是一个有帮助的AI助手。" },
        { role: "user", content: prompt },
      ],
      max_tokens: Number(max_tokens),
      temperature: Number(temperature),
    });

    const reply = completion.choices[0].message.content;
    const usage = completion.usage;

    logger.info(`✅ 响应成功 | Token 使用: ${JSON.stringify(usage)}`);

    res.json({ reply, model: DEEPSEEK_MODEL, usage });
  } catch (err) {
    logger.error(`❌ API 调用失败: ${err.message}`);
    res.status(502).json({
      error: "DeepSeek API 调用失败",
      detail: err.message,
    });
  }
});

// ---------- 启动服务器 ----------
app.listen(PORT, () => {
  logger.info("============================================");
  logger.info(`  🚀 Node.js 服务已启动`);
  logger.info(`  地址: http://localhost:${PORT}`);
  logger.info(`  Chat API: POST http://localhost:${PORT}/chat`);
  logger.info(`  模型: ${DEEPSEEK_MODEL}`);
  logger.info("============================================");
});
