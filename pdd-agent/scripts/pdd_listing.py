#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多商品上架助手 - 批量生成上架方案
"""
import csv, json, os, sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 拼多多标题生成 ──
def gen_title(product, style="精准型"):
    name = product.get("商品名称", "")
    cat = product.get("品类", "通用")
    pts = product.get("卖点", "").split("/")
    scene = product.get("使用场景", "")
    crowd = product.get("目标人群", "")
    extra = product.get("标题补充词", "")
    
    if style == "精准型":
        t = f"{name}{cat}{pts[0] if pts else ''}{scene}{crowd}".strip()[:30]
    elif style == "引流型":
        # 拼多多引流型：热搜词+产品+价格暗示
        t = f"{pts[0] if pts else ''}{name}{cat}{extra}".strip()[:30]
    else:  # 长尾型
        t = f"{scene}{crowd}{name}{pts[0] if pts else ''}{cat}".strip()[:30]
    
    # 保证30字以内
    cut = t[:30]
    return cut if cut else name[:30]

# ── PDD SKU 生成（带引流/主推/锚点策略） ──
def gen_sku(product):
    name = product.get("商品名称", "")
    price_str = product.get("目标售价", "49.9")
    cost_str = product.get("成本价", "20")
    try:
        price = float(price_str)
        cost = float(cost_str)
    except:
        price, cost = 49.9, 20.0
    
    cat = product.get("品类", "")
    
    if "服装" in cat or "T恤" in name or "衣服" in name:
        # 服装类：颜色+尺码
        yinliu = round(price * 0.7, 1)
        zhutui = round(price * 0.9, 1)
        return [
            {"type": "引流", "spec": "白色/M（体验装）", "price": yinliu, "stock": 50, "note": "引流拉权重"},
            {"type": "引流", "spec": "黑色/M（体验装）", "price": yinliu, "stock": 50, "note": "引流拉权重"},
            {"type": "主推", "spec": "白色/L（最划算🔥）", "price": zhutui, "stock": 200, "note": "主力利润款"},
            {"type": "主推", "spec": "黑色/L（最划算🔥）", "price": zhutui, "stock": 200, "note": "主力利润款"},
            {"type": "主推", "spec": "白色/XL（最划算🔥）", "price": zhutui, "stock": 200, "note": "主力利润款"},
            {"type": "锚点", "spec": "白色/2件装（全家桶）", "price": round(price * 1.6, 1), "stock": 30, "note": "衬托主推划算"},
        ]
    elif "食品" in cat or "零食" in cat:
        yinliu = round(price * 0.6, 1)
        zhutui = round(price * 0.9, 1)
        return [
            {"type": "引流", "spec": "1袋体验装", "price": yinliu, "stock": 100, "note": "引流拉权"},
            {"type": "主推", "spec": "3袋实惠装🔥", "price": round(zhutui * 2.5, 1), "stock": 200, "note": "主力推荐"},
            {"type": "锚点", "spec": "5袋超值装", "price": round(zhutui * 4.0, 1), "stock": 50, "note": "锚点款"},
        ]
    else:
        yinliu = round(price * 0.65, 1)
        zhutui = round(price * 0.9, 1)
        return [
            {"type": "引流", "spec": "基础款", "price": yinliu, "stock": 50, "note": "引流拉权重"},
            {"type": "主推", "spec": "升级款🔥", "price": zhutui, "stock": 100, "note": "主力利润款"},
            {"type": "锚点", "spec": "豪华全套", "price": round(price * 1.4, 1), "stock": 20, "note": "衬托主推"},
        ]

# ── 主图方案 ──
def gen_images(product):
    name = product.get("商品名称", "")
    pts = product.get("卖点", "").split("/")
    return [
        f"首图：{name}实拍白底 + 大字「{' '.join(pts[:2])}」+ 价格",
        f"图2：核心卖点图（{', '.join(pts[:4])}）配图标",
        f"图3：细节/材质特写（高清放大）",
        f"图4：场景图（{product.get('使用场景','使用场景')}展示）",
        f"图5：规格/尺码/对比图",
    ]

# ── 关键词生成 ──
def gen_keywords(product):
    name = product.get("商品名称", "")
    cat = product.get("品类", "")
    pts = product.get("卖点", "").split("/")
    scene = product.get("使用场景", "")
    
    base = [name, cat] + [s.strip() for s in pts]
    search = [
        f"{name}{cat}",
        f"{cat}{name}",
        f"{name}2026新款",
        f"{name} 拼多多",
        f"{scene}{name}",
        f"{name}热销",
        f"便宜{name}",
        f"好评{name}",
    ]
    # 去重
    seen = set()
    result = []
    for w in base + search:
        if w and w not in seen:
            result.append(w)
            seen.add(w)
    return result[:15]

# ── 主函数 ──
def main():
    import argparse
    parser = argparse.ArgumentParser(description="拼多多商品上架助手")
    parser.add_argument("--input", default="products.csv")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        input_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "products", args.input)
    if not os.path.exists(input_path):
        print("❌ 找不到商品文件！")
        return
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        products = list(csv.DictReader(f))
    
    print(f"\n📦 共 {len(products)} 个商品 → 拼多多上架方案生成中...")
    
    output_dir = args.output or os.path.join(os.path.dirname(__file__), "..", "workspace", "products", "listings")
    os.makedirs(output_dir, exist_ok=True)
    
    for i, prod in enumerate(products, 1):
        name = prod.get("商品名称", f"商品{i}")
        print(f"\n  [{i}/{len(products)}] {name}")
        
        titles = {s: gen_title(prod, s) for s in ["精准型", "引流型", "长尾型"]}
        skus = gen_sku(prod)
        images = gen_images(prod)
        kws = gen_keywords(prod)
        
        # 写文件
        fp = os.path.join(output_dir, f"{datetime.now().strftime('%Y%m%d')}_{name}_拼多多.md")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(f"# {name} — 拼多多上架方案\n")
            f.write(f"**生成**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            
            f.write("## 📝 标题方案\n\n")
            for k, v in titles.items():
                f.write(f"- **{k}**：{v}（{len(v)}字）\n")
            
            f.write("\n## 💰 SKU方案\n\n")
            f.write("| 类型 | 规格 | 价格 | 库存 | 说明 |\n")
            f.write("|------|------|------|------|------|\n")
            for s in skus:
                emoji = {"引流":"🎣","主推":"🔥","锚点":"📍"}.get(s["type"],"")
                f.write(f"| {emoji}{s['type']} | {s['spec']} | ¥{s['price']} | {s['stock']} | {s['note']} |\n")
            
            f.write("\n## 🖼 主图方案\n\n")
            for img in images:
                f.write(f"- {img}\n")
            
            f.write("\n## 🏷 热搜关键词\n\n")
            f.write(" ".join(kws) + "\n")
        
        print(f"     ✓ 已生成 → {fp}")
    
    print(f"\n✅ 全部完成！输出：{output_dir}")

if __name__ == "__main__":
    main()
