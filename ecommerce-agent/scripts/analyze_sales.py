#!/usr/bin/env python3
"""
运营数据分析脚本
分析销售数据，生成日报/周报
"""
import csv
import sys

# Windows GBK fix for emoji
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
from datetime import datetime, timedelta

def analyze_sales(csv_path):
    """分析销售数据"""
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        sales = list(reader)
    
    if not sales:
        return {"error": "没有数据"}
    
    total_revenue = 0
    total_orders = 0
    product_sales = {}  # {商品名: {"revenue": x, "orders": y, "qty": z}}
    
    for row in sales:
        product = row.get("商品名称", "未知")
        qty = int(row.get("数量", 0))
        price = float(row.get("单价", 0))
        revenue = qty * price
        
        total_revenue += revenue
        total_orders += qty
        
        if product not in product_sales:
            product_sales[product] = {"revenue": 0, "orders": 0, "qty": 0}
        product_sales[product]["revenue"] += revenue
        product_sales[product]["orders"] += 1
        product_sales[product]["qty"] += qty
    
    sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["qty"], reverse=True)
    
    return {
        "总销售额": round(total_revenue, 2),
        "总订单数": total_orders,
        "客单价": round(total_revenue / total_orders, 2) if total_orders else 0,
        "商品数": len(product_sales),
        "爆款TOP10": [
            {"name": name, "销量": data["qty"], "销售额": round(data["revenue"], 2)}
            for name, data in sorted_products[:10]
        ],
        "滞销品": [
            {"name": name, "销量": data["qty"]}
            for name, data in sorted_products[-3:] if data["qty"] <= 2
        ],
    }

def generate_report(data, report_type="日报"):
    """生成 Markdown 报告"""
    now = datetime.now()
    report = f"""# 运营{report_type} {now.strftime('%Y-%m-%d')}

## 📊 核心数据一览
"""
    report += f"""
| 指标 | 数值 |
|------|------|
| 总销售额 | ¥{data['总销售额']} |
| 总订单数 | {data['总订单数']} |
| 客单价 | ¥{data['客单价']} |
| 动销商品数 | {data['商品数']} |
"""
    
    report += "\n## 🔥 爆款 TOP10\n\n| 排名 | 商品 | 销量 | 销售额 |\n|:---:|------|:---:|:------:|\n"
    for i, item in enumerate(data["爆款TOP10"], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}")
        report += f"| {medal} | {item['name']} | {item['销量']}件 | ¥{item['销售额']} |\n"
    
    if data.get("滞销品"):
        report += "\n## ⚠️ 滞销预警\n\n"
        for item in data["滞销品"]:
            report += f"- {item['name']} — 仅售出 {item['销量']}件，建议促销/降价/下架\n"
    
    report += f"""
## 💡 运营建议
"""
    if data['总订单数'] > 0:
        report += f"""
基于今日数据分析：
1. **爆款强化** — {'、'.join([item['name'] for item in data['爆款TOP10'][:3]])} 表现强劲，可加大推广
2. **库存管理** — 需确保爆款商品库存充足
3. **滞销处理** — 对滞销品考虑捆绑促销或清仓
"""
    
    report += f"\n\n---\n*报告生成时间：{now.strftime('%Y-%m-%d %H:%M')}*\n"
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser(description="销售数据分析")
    parser.add_argument("--input", default="", help="销售CSV文件")
    parser.add_argument("--type", default="日报", choices=["日报", "周报", "月报"])
    args = parser.parse_args()
    
    # 找最新的销售数据文件
    data_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "products")
    
    if args.input:
        csv_path = args.input
        if not os.path.exists(csv_path):
            csv_path = os.path.join(data_dir, args.input)
    else:
        # 自动找最新的 sales_*.csv
        csv_files = [f for f in os.listdir(data_dir) if f.startswith("sales_") and f.endswith(".csv")]
        if not csv_files:
            print("❌ 没有找到销售数据文件")
            print("请将销售数据保存为 workspace/products/sales_YYYY-MM-DD.csv")
            return
        csv_path = os.path.join(data_dir, sorted(csv_files)[-1])
    
    print(f"📊 分析文件：{csv_path}")
    data = analyze_sales(csv_path)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        return
    
    report = generate_report(data, args.type)
    
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "reports", "daily")
    os.makedirs(reports_dir, exist_ok=True)
    
    report_path = os.path.join(reports_dir, f"{datetime.now().strftime('%Y-%m-%d')}.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ 报告已生成：{report_path}")
    print("\n" + report)

if __name__ == "__main__":
    main()
