# Codex 电商运营智能体 — 完整方案

> 参考抖音创作者：给我加冰🧊、阳雨Ai、大鲸AI 的思路，整合出的可运行方案

---

## 一、整体架构

```
┌─────────────────────────────────────────────────┐
│                  Codex 5.x                       │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │  AGENTS.md  │  │  Skills/ │  │  Workspace │  │
│  │  (人格定义)  │  │  (技能)   │  │  (数据/文件) │  │
│  └──────┬──────┘  └─────┬────┘  └──────┬─────┘  │
│         │               │              │         │
│  ┌──────┴───────────────┴──────────────┴──────┐  │
│  │          MCP Tools (外部集成层)              │  │
│  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              电商运营工作流                        │
│  ┌──────────┐ ┌─────────┐ ┌──────┐ ┌────────┐  │
│  │  商品上架  │ │ 素材生成  │ │ 数据分析 │ │ 社媒运营 │  │
│  └──────────┘ └─────────┘ └──────┘ └────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 二、第一步：AGENTS.md — 定义运营助理人格

> 在 Codex 工作区根目录创建 `AGENTS.md`

```markdown
# 电商运营助理 AI

## 角色定位
你是我的电商运营助理，擅长商品管理、数据分析、内容生成和平台运营。

## 核心能力
- 商品上架与优化（标题/描述/SKU/主图）
- 批量素材生成（产品图片/视频/详情页）
- 数据分析（销量/库存/竞品分析）
- 社媒内容运营（小红书/抖音文案）

## 工作原则
1. 所有操作前先确认，不擅自执行
2. 数据优先，用数据说话
3. 批量任务优先，减少重复劳动
4. 主动汇报进度和异常

## 常用数据源
- 商品数据：workspace/products/
- 素材模板：workspace/templates/
- 分析报告：workspace/reports/
- SKU 规则：workspace/rules/sku-rules.md
```

---

## 三、第二步：Skills 体系 — 核心技能模块

### Skill 1：商品自动上架

在 `skills/product-lister/SKILL.md` 中定义：

```markdown
# 商品上架助手

## 功能
根据商品信息批量生成平台对应的上架内容，包括标题优化、描述撰写、SKU 生成、主图建议。

## 输入
- 商品名称 / 品类
- 核心卖点（3-5点）
- 价格区间
- 平台（淘宝/拼多多/抖音小店）
- 图片素材（可选）

## 输出
- 优化后的商品标题（3个版本）
- 详情页文案
- SKU 方案（规格/价格/库存）
- 主图设计方案

## 调用方式
在 Codex 中直接描述商品信息即可触发
```

### Skill 2：批量化内容生成

参考 阳雨Ai 的思路（飞书多维表 + 工作流），用 Codex 的 Skills + MCP 实现：

```markdown
# 批量内容生成

## 功能
根据商品清单批量生成产品图片、视频脚本、营销文案

## 工作流
1. 读取商品清单（CSV/飞书多维表）
2. 逐条生成文案和图片描述
3. 调用 MCP 工具生成图片/视频
4. 输出到指定文件夹

## 支持的生成类型
- 主图（白底图/场景图） 
- 详情页长图
- 短视频脚本（15-60秒）
- 直播话术
```

### Skill 3：运营数据分析

```markdown
# 运营数据分析

## 功能
分析店铺运营数据，生成可读报告

## 分析维度
- 销量趋势（日/周/月）
- 爆款/滞销品识别
- 竞品价格监控
- ROI 分析
- 库存预警

## 输出格式
Markdown 报告 + CSV 数据表
```

---

## 四、第三步：项目目录结构

```
ecommerce-agent/
├── AGENTS.md                    # 人格定义（上面已写好）
├── SKILLS.md                    # 技能索引
│
├── skills/                      # 技能目录
│   ├── product-lister/
│   │   └── SKILL.md             # 商品上架技能
│   ├── content-generator/
│   │   └── SKILL.md             # 内容生成技能
│   ├── data-analyzer/
│   │   └── SKILL.md             # 数据分析技能
│   └── social-media/
│       └── SKILL.md             # 社媒运营技能
│
├── workspace/                   # 工作区数据
│   ├── products/                # 商品数据
│   │   ├── products.csv         # 商品清单
│   │   └── templates/           # 模板文件
│   ├── content/                 # 生成的素材
│   │   ├── images/
│   │   └── videos/
│   ├── reports/                 # 分析报告
│   └── rules/                   # 业务规则
│       ├── sku-rules.md
│       └── pricing-rules.md
│
├── scripts/                     # 自动化脚本
│   ├── generate_listing.py      # 批量生成上架内容
│   ├── batch_images.py          # 批量图片处理
│   └── analyze_sales.py         # 销售数据分析
│
└── mcp-config.json              # MCP 工具配置
```

---

## 五、MCP 工具集成（扩展能力）

Codex 的 MCP 可以接入各种外部工具，电商运营推荐接入：

| 工具 | 用途 | 说明 |
|------|------|------|
| **文件系统** | 读写 CSV/JSON/Excel | Codex 内置 |
| **浏览器** | 抓取竞品数据 / 店铺后台 | MCP Playwright |
| **图像生成** | 生成产品图 / 详情页 | Midjourney / DALL-E |
| **飞书 API** | 多维表数据 / 消息推送 | 阳雨Ai 的路线 |
| **数据库** | 商品数据 / 订单数据 | SQLite / MySQL |
| **Puppeteer** | 自动化操作网页 | 自动上架到平台 |

---

## 六、快速启动

### 1️⃣ 安装 Codex

```
# 如果你还没装：
npm install -g @openai/codex
# 或从官网下载安装包
# https://codex.ai
```

### 2️⃣ 创建项目

```bash
mkdir ecommerce-agent
cd ecommerce-agent
codex init
```

### 3️⃣ 写入 AGENTS.md

把上面的 AGENTS.md 内容粘贴到项目根目录

### 4️⃣ 创建 Skills 目录

```bash
mkdir -p skills/product-lister
mkdir -p skills/content-generator
mkdir -p skills/data-analyzer
mkdir -p workspace/products
mkdir -p workspace/content/images
mkdir -p workspace/reports
```

把上面的 SKILL.md 分别写入对应目录

### 5️⃣ 开始使用

在项目目录启动 Codex，然后直接跟它说：

```
我现在要在抖音小店上架一款新产品：
- 商品：XXX（你的产品）
- 卖点：XXX
- 价格：XXX
- 帮我生成标题、描述和主图方案
```

---

## 七、进阶：飞书工作流自动化

参考 **阳雨Ai** 的做法，整合飞书实现更强大的自动化：

### 架构

```
用户 → 飞书多维表（提交任务）
         ↓
    飞书工作流（监听新记录）
         ↓
    Codex Agent（处理任务）
         ↓
    结果写回多维表
         ↓
    自动推送通知
```

### 简单的 Python 实现

```python
# scripts/feishu_workflow_bridge.py
# 这个脚本监听飞书多维表的新记录，调用 Codex 处理

import json
import subprocess

def process_task(task_data):
    """调用 Codex 处理任务"""
    product_name = task_data.get("商品名称")
    platform = task_data.get("目标平台")
    
    prompt = f"""
    请为以下商品生成上架内容：
    商品：{product_name}
    平台：{platform}
    
    输出格式：
    1. 标题（3个版本）
    2. 描述文案
    3. SKU 方案
    4. 主图建议
    """
    
    # 通过 Codex CLI 处理
    result = subprocess.run(
        ["codex", "run", "--prompt", prompt],
        capture_output=True, text=True, timeout=60
    )
    
    return result.stdout

# 配合飞书 API 读取/写入多维表
# ...
```

---

## 八、场景示例

### 场景 1：日常上架

> **你**：帮我上架10个夏季新款T恤到拼多多
>
> **Codex**：好的，我先读取 workspace/products/summer-tshirts.csv
> 数据共10条，开始逐条处理...
> 1. 纯棉印花T恤 → 标题已生成 ✓
> 2. 冰丝速干T恤 → 标题已生成 ✓
> ...
> 全部完成！已保存到 workspace/content/listings/ 目录

### 场景 2：每日数据

> **你**：看看昨天店铺数据
>
> **Codex**：正在分析 workspace/data/sales_20260620.csv...
> 昨日数据简报：
> - 总销售额：¥8,532
> - 订单数：47
> - 爆款：纯棉T恤（13单）
> - 滞销：棒球帽（0单）
> - 建议：棒球帽考虑降价或搭配促销

### 场景 3：批量素材

> **你**：把这10个商品生成抖音短视频脚本
>
> **Codex**：正在逐商品生成...
> 每个商品我做了3个脚本版本（15s/30s/60s）
> 已保存到 workspace/content/videos/scripts/

---

## 九、后续可扩展方向

1. ✅ **接入真实电商平台 API** — 直接自动上架（需授权）
2. ✅ **整合飞书/钉钉** — 移动端提交任务，消息推送
3. ✅ **接入 AI 作图** — Midjourney / DALL-E 自动生成主图
4. ✅ **定时任务** — 每日自动出数据报告
5. ✅ **多平台同步** — 淘宝/拼多多/抖音一键同步上架
6. ✅ **评论分析** — 自动分析用户评价提取优化建议
7. ✅ **智能定价** — 根据竞品数据自动调价

---

## 十、参考创作者

| 创作者 | 内容方向 |
|--------|---------|
| **给我加冰🧊** | Codex 做电商运营助理（商品上架） |
| **阳雨Ai** | Codex+飞书+工作流，日产1000+视频 |
| **大鲸AI** | Codex 焚诀系列（工作区/Skills/MCP 高级用法） |
| **瑞哥那** | Codex 完整教程（9.9万👍） |
| **川大猿** | Codex 安装配置+DeepSeek 接入 |
| **文走走的Ai分享** | Codex 插件生态详解 |
