#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDD运营日报 + 竞品分析 生成器
"""
import csv, json, os, sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def analyze_sales(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    
    total_rev = 0
    total_orders = 0
    prod_data = {}
    
    for r in rows:
        name = r.get("商品名称", "未知")
        qty = int(r.get("数量", 0))
        unit = float(r.get("单价", 0))
        rev = qty * unit
        total_rev += rev
        total_orders += qty
        if name not in prod_data:
            prod_data[name] = {"qty": 0, "rev": 0, "orders": 0}
        prod_data[name]["qty"] += qty
        prod_data[name]["rev"] += rev
        prod_data[name]["orders"] += 1
    
    sorted_prods = sorted(prod_data.items(), key=lambda x: x[1]["qty"], reverse=True)
    
    return {
        "总销售额": round(total_rev, 2),
        "总订单": total_orders,
        "客单价": round(total_rev / total_orders, 2) if total_orders else 0,
        "动销商品": len(prod_data),
        "爆款TOP": [{"name": n, "销量": d["qty"], "销售额": round(d["rev"], 2), "占比": f"{round(d['rev']/total_rev*100,1)}%"} for n, d in sorted_prods],
        "滞销": [{"name": n, "销量": d["qty"]} for n, d in reversed(sorted_prods) if d["qty"] <= 3],
    }

def gen_report(data):
    now = datetime.now()
    r = f"""# 📊 拼多多运营日报 {now.strftime('%Y-%m-%d')}

## 核心数据一览

| 指标 | 数值 |
|------|------|
| 💰 总销售额 | ¥{data['总销售额']} |
| 📦 总订单数 | {data['总订单']} |
| 👤 客单价 | ¥{data['客单价']} |
| 📊 动销商品 | {data['动销商品']}个 |

## 🔥 商品排名
"""
    medals = {1:"🥇",2:"🥈",3:"🥉"}
    for i, p in enumerate(data["爆款TOP"], 1):
        medal = medals.get(i, f"  {i}")
        r += f"| {medal} | {p['name']} | {p['销量']}件 | ¥{p['销售额']} | {p['占比']} |\n"
    
    if data.get("滞销"):
        r += "\n## ⚠️ 滞销预警\n"
        for p in data["滞销"]:
            r += f"- {p['name']}：仅售{p['销量']}件，建议降价/搭售/下架\n"
    
    # 智能建议
    r += "\n## 💡 运营建议\n"
    if data['总订单'] > 0:
        top = data['爆款TOP'][0]
        r += f"1. **爆款强化** — {top['name']} 占比 {top['占比']}，可加大全站推广预算\n"
        r += f"2. **利润分析** — 毛利率需控制在20%以上（含退款损耗）\n"
    if data.get("滞销"):
        r += f"3. **清仓建议** — 滞销品考虑降价30%或设置满减搭售\n"
    
    r += f"\n---\n*生成：{now.strftime('%Y-%m-%d %H:%M')}*"
    return r

def main():
    import argparse
    parser = argparse.ArgumentParser(description="PDD运营日报")
    parser.add_argument("--input", default="")
    args = parser.parse_args()
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "products")
    
    if args.input:
        csv_path = args.input if os.path.exists(args.input) else os.path.join(data_dir, args.input)
    else:
        files = [f for f in os.listdir(data_dir) if f.startswith("sales_") and f.endswith(".csv")]
        if not files:
            print("❌ workspace/products/ 下没有销售数据文件")
            return
        csv_path = os.path.join(data_dir, sorted(files)[-1])
    
    d = analyze_sales(csv_path)
    if not d:
        print("❌ 数据为空")
        return
    
    report = gen_report(d)
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "reports", "daily")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{datetime.now().strftime('%Y-%m-%d')}_pdd.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(report)
    print(f"\n✅ 报告已保存：{out_path}")

if __name__ == "__main__":
    main()
