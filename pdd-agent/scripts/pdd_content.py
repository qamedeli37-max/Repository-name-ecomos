#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拼多多内容素材生成器
主图方案 / 详情页 / 短视频脚本 / SKU规划
"""
import csv, json, os, sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── AI 作图提示词（PDD风格） ──
def gen_image_prompts(product):
    name = product.get("商品名称", "")
    pts = product.get("卖点", "").split("/")
    scene = product.get("使用场景", "日常使用")
    style = product.get("风格", "电商产品摄影")
    
    return {
        "首图白底": f"Product photography, {name}, pure white background, centered, studio lighting, high detail, 8K, pinduoduo style, clean and bright, commercial photo",
        "场景图": f"Lifestyle photography, {name} in use, {scene}, natural lighting, casual style, realistic, warm tones, 8K, product in context",
        "细节图": f"Macro detail shot, {name}, texture closeup, {pts[0] if pts else 'premium quality'}, soft diffused light, shallow depth of field, 8K, product detail",
        "卖点图": f"Infographic style, {name}, key features highlighted: {' '.join(pts[:3])}, clean layout, bright colors, 8K, commercial infographic",
    }

# ── 30秒抖音风格短视频脚本 ──
def gen_video_script(product):
    name = product.get("商品名称", "")
    price = product.get("目标售价", "49.9")
    pts = product.get("卖点", "").split("/")
    
    return f"""## {name} — 30秒带货脚本（PDD抖音风格）

🎵 BGM：热门快节奏卡点音乐
🎤 口播：热情、真实分享感

[0-3s] 开头钩子
画面：痛点场景快切
字幕：你还在花XXX买这个？

[3-12s] 产品亮相
画面：产品旋转展示 + 细节特写
口播：拼多多搜{name}，看看这个！
字幕：{name}

[12-22s] 卖点展示
画面：逐条展示{len(pts)}个核心卖点
{'、'.join([f'画面：{p.strip()}' for p in pts[:4]])}

[22-28s] 价格冲击
画面：价格大字展示 + 倒计时
口播：现在只要 ¥{price}
字幕：🔥 限时福利 🔥

[28-30s] 引导
画面：引导点击购买
口播：左下角，冲就完了！

🏷 #好物推荐 #{name.replace(' ','')} #拼多多好物 #性价比"""

# ── 详情页文案（PDD短平快风格） ──
def gen_detail(product):
    name = product.get("商品名称", "")
    pts = product.get("卖点", "").split("/")
    price = product.get("目标售价", "49.9")
    material = product.get("材质", "")
    
    r = f"""## {name}

🔥 为什么要买它？
{chr(10).join([f'{i+1}. ✅ {p.strip()}' for i, p in enumerate(pts[:5])])}

💰 今日特价：¥{price}
"""
    if material:
        r += f"\n📦 材质：{material}\n"
    
    r += f"""
📏 规格选择
（详见SKU）

🚚 发货
- 48小时发货
- 极速退款
- 7天无理由

💡 温馨提示
因光线/显示器差异，颜色以实物为准
"""
    return r

def main():
    import argparse
    parser = argparse.ArgumentParser(description="PDD素材生成器")
    parser.add_argument("--input", default="products.csv")
    parser.add_argument("--type", default="all", choices=["all", "images", "video", "detail"])
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        input_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "products", args.input)
    if not os.path.exists(input_path):
        print("❌ 找不到商品文件！")
        return
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        products = list(csv.DictReader(f))
    
    print(f"\n📦 共 {len(products)} 个商品\n")
    
    base = os.path.join(os.path.dirname(__file__), "..", "workspace", "content")
    os.makedirs(os.path.join(base, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(base, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(base, "details"), exist_ok=True)
    
    for i, prod in enumerate(products, 1):
        name = prod.get("商品名称", f"商品{i}")
        sn = name.replace("/", "_").replace("\\", "_")
        print(f"[{i}/{len(products)}] {name}")
        
        if args.type in ("all", "images"):
            prompts = gen_image_prompts(prod)
            fp = os.path.join(base, "prompts", f"{sn}_AI提示词.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(f"# {name} — AI作图提示词\n\n")
                for k, v in prompts.items():
                    f.write(f"## {k}\n```\n{v}\n```\n\n")
            print(f"  ✓ AI作图提示词")
        
        if args.type in ("all", "video"):
            script = gen_video_script(prod)
            fp = os.path.join(base, "scripts", f"{sn}_30s脚本.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(script)
            print(f"  ✓ 短视频脚本")
        
        if args.type in ("all", "detail"):
            detail = gen_detail(prod)
            fp = os.path.join(base, "details", f"{sn}_详情页.md")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(detail)
            print(f"  ✓ 详情页文案")
    
    print(f"\n✅ 全部完成！输出：{base}")

if __name__ == "__main__":
    main()
