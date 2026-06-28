# 拼多多电商运营助手 — 技能索引

## 📂 项目结构
```
pdd-agent/
├── AGENTS.md                   ← 运营助理人格定义
├── skills/
│   ├── product-listing/        ← 商品上架+SKU策略
│   ├── data-analysis/          ← 运营数据分析
│   ├── promotion/              ← 推广与活动运营
│   └── content/                ← 内容与素材生成
├── scripts/
│   ├── pdd_listing.py          ★ 商品上架批量生成
│   ├── pdd_daily.py            ★ 运营日报生成
│   └── pdd_content.py          ★ 素材/脚本/详情生成
└── workspace/
    ├── products/               ← 商品数据/CSV
    ├── content/                ← 生成的素材
    ├── reports/                ← 日报/分析报告
    └── knowledge/              ← 拼多多运营知识库
```

## 🚀 快速使用

```bash
# 1. 批量生成拼多多上架方案
py scripts\pdd_listing.py --input products.csv

# 2. 生成运营日报
py scripts\pdd_daily.py --input sales.csv

# 3. 批量生成素材
py scripts\pdd_content.py --input products.csv
```
