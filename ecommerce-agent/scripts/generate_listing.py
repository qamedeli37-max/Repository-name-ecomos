#!/usr/bin/env python3
"""
批量生成商品上架内容
用法: python generate_listing.py --input products.csv --platform 拼多多
"""
import csv
import sys

# Windows GBK fix for emoji
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
import sys
from datetime import datetime

# 模板
TITLE_TEMPLATES = {
    "精准型": "{卖点1} {卖点2} {商品名} {品类}",
    "引流型": "{价格}起！{卖点1} {商品名} {品类} {场景}",
    "长尾词型": "{场景} {商品名} {卖点1} {卖点2} {品类} {人群}"
}

PLATFORM_RULES = {
    "淘宝": {"max_title": 30, "max_images": 5},
    "拼多多": {"max_title": 30, "max_images": 5},
    "抖音小店": {"max_title": 20, "max_images": 4},
    "小红书": {"max_title": 20, "max_images": 9},
}

def generate_title(product, platform, version="精准型"):
    """生成标题"""
    template = TITLE_TEMPLATES.get(version, TITLE_TEMPLATES["精准型"])
    title = template.format(
        商品名=product.get("商品名称", ""),
        品类=product.get("品类", ""),
        卖点1=product.get("卖点", "").split("/")[0] if "/" in product.get("卖点", "") else product.get("卖点", ""),
        卖点2=product.get("卖点", "").split("/")[-1] if "/" in product.get("卖点", "") else "",
        价格=product.get("目标售价", ""),
        场景=product.get("使用场景", ""),
        人群=product.get("目标人群", ""),
    )
    max_len = PLATFORM_RULES.get(platform, {}).get("max_title", 30)
    return title[:max_len]

def generate_sku(product):
    """生成 SKU 方案"""
    name = product.get("商品名称", "")
    price = product.get("目标售价", "49.9")
    
    # 根据品类推测 SKU
    category = product.get("品类", "")
    
    if "服装" in category or "T恤" in name or "衣服" in name or "穿搭" in category:
        return [
            {"规格": "白色/M", "价格": price, "库存": 50},
            {"规格": "白色/L", "价格": price, "库存": 50},
            {"规格": "白色/XL", "价格": price, "库存": 50},
            {"规格": "黑色/M", "价格": price, "库存": 50},
            {"规格": "黑色/L", "价格": price, "库存": 50},
            {"规格": "黑色/XL", "价格": price, "库存": 50},
        ]
    elif "食品" in category or "零食" in category:
        return [
            {"规格": "1袋装", "价格": price, "库存": 100},
            {"规格": "3袋装(实惠装)", "价格": round(float(price) * 2.5, 1), "库存": 80},
            {"规格": "5袋装(超值装)", "价格": round(float(price) * 4.0, 1), "库存": 50},
        ]
    else:
        return [
            {"规格": "标准款", "价格": price, "库存": 50},
        ]

def generate_description(product):
    """生成详情页文案"""
    name = product.get("商品名称", "")
    selling_points = product.get("卖点", "").split("/")
    material = product.get("材质", "")
    
    desc = f"""## ✨ {name}

### 📌 为什么选它？
"""
    for i, point in enumerate(selling_points, 1):
        desc += f"{i}. 👍 {point.strip()}\n"
    
    if material:
        desc += f"\n### 🧵 材质工艺\n{material}\n"
    
    desc += """
### 📏 尺码建议
（请根据你的具体商品填写尺码表）

### 📦 售后保障
- 7天无理由退换
- 质量问题包邮退换
- 24小时发货

### 💡 温馨提示
因拍摄光线和显示器不同，颜色可能有细微差异，以实物为准。
"""
    return desc

def generate_keywords(product):
    """生成搜索关键词"""
    name = product.get("商品名称", "")
    category = product.get("品类", "")
    selling_points = product.get("卖点", "").split("/")
    
    keywords = [name, category]
    keywords.extend([s.strip() for s in selling_points])
    keywords.extend([
        f"{name} {category}",
        f"2026新款{name}",
        f"{name}推荐",
        f"{name}测评",
    ])
    return keywords

def process_product(product, platform):
    """处理单个商品，生成完整上架内容"""
    result = {
        "商品名称": product.get("商品名称", ""),
        "平台": platform,
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "标题": {
            "精准型": generate_title(product, platform, "精准型"),
            "引流型": generate_title(product, platform, "引流型"),
            "长尾词型": generate_title(product, platform, "长尾词型"),
        },
        "SKU方案": generate_sku(product),
        "详情文案": generate_description(product),
        "主图建议": [
            "首图：白底图，产品居中，突出轮廓",
            "图2：卖点图（用文字标注核心优势）",
            f"图3：场景图（展示{product.get('使用场景', '使用场景')}）",
            "图4：细节图（材质/做工/尺寸）",
            "图5：尺码表/对比图",
        ],
        "关键词建议": generate_keywords(product),
    }
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="批量生成商品上架内容")
    parser.add_argument("--input", default="products.csv", help="商品CSV文件")
    parser.add_argument("--platform", default="拼多多", choices=["淘宝", "拼多多", "抖音小店", "小红书"])
    parser.add_argument("--output", default="", help="输出目录")
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        input_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "products", args.input)
    
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件: {args.input}")
        print("请在 workspace/products/ 目录下放置 products.csv")
        return
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        products = list(reader)
    
    print(f"📦 共 {len(products)} 个商品，平台：{args.platform}")
    
    output_dir = args.output or os.path.join(os.path.dirname(__file__), "..", "workspace", "products", "listings")
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    for i, product in enumerate(products, 1):
        name = product.get("商品名称", f"商品{i}")
        print(f"  [{i}/{len(products)}] 处理：{name}")
        
        result = process_product(product, args.platform)
        all_results.append(result)
        
        # 单个商品保存
        filename = f"{datetime.now().strftime('%Y%m%d')}_{name}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {name} — {args.platform}上架方案\n\n")
            f.write(f"**生成时间**：{result['生成时间']}\n\n")
            
            f.write("## 标题方案\n\n")
            for k, v in result["标题"].items():
                f.write(f"- **{k}**：{v}\n")
            
            f.write("\n## SKU 方案\n\n")
            f.write("| 规格 | 价格 | 库存 |\n")
            f.write("|------|------|------|\n")
            for sku in result["SKU方案"]:
                f.write(f"| {sku['规格']} | ¥{sku['价格']} | {sku['库存']} |\n")
            
            f.write("\n## 主图建议\n\n")
            for img in result["主图建议"]:
                f.write(f"- {img}\n")
            
            f.write("\n## 详情文案\n\n")
            f.write(result["详情文案"])
            
            f.write("\n\n## 关键词建议\n\n")
            f.write(", ".join(result["关键词建议"]))
        
        print(f"    ✓ 已保存到 {filepath}")
    
    # 汇总 JSON
    json_path = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d')}_汇总.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 全部完成！共生成 {len(products)} 个商品的上架方案")
    print(f"📁 输出目录：{output_dir}")

if __name__ == "__main__":
    main()
