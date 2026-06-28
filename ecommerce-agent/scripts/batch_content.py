#!/usr/bin/env python3
"""
批量内容生成脚本
生成商品图片提示词、短视频脚本、小红书文案
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

def generate_image_prompt(product):
    """生成 AI 作图提示词"""
    name = product.get("商品名称", "")
    selling_points = product.get("卖点", "").split("/")
    style = product.get("风格", "极简商业摄影")
    
    prompts = {
        "白底图": f"Professional product photography, {name}, white background, studio lighting, centered composition, 8K, photorealistic, clean edges, commercial catalog style",
        "场景图": f"Lifestyle photography, {name} in use, natural lighting, aesthetic composition, {style}, warm tones, realistic, 8K, commercial photography",
        "卖点图": f"Detail macro shot, {name}, texture closeup, {selling_points[0] if selling_points else 'premium quality'}, soft lighting, depth of field, 8K, product detail photography",
        "模特图": f"Model wearing {name}, street style photography, urban setting, natural poses, candid look, golden hour lighting, fashion editorial style, 8K",
    }
    return prompts

def generate_short_video_script(product, duration=30):
    """生成短视频脚本"""
    name = product.get("商品名称", "")
    price = product.get("目标售价", "49.9")
    selling_points = product.get("卖点", "").split("/")
    
    if duration <= 15:
        return f"""## {name} — 15s 快闪脚本

• BGM：热门卡点音乐

[0-3s] 产品特写 + 大字：夏日救星来了！
[3-8s] 展示产品核心卖点：{'、'.join(selling_points[:2])}
[8-12s] 价格展示：只要¥{price}
[12-15s] 引导：左下角冲！

#好物推荐 #{name}"""
    
    elif duration <= 30:
        return f"""## {name} — 30s 种草脚本

• BGM：轻快节奏
• 口播风格：真实分享感

[0-3s] 开头钩子
画面：夏天出汗尴尬场景
文字：你夏天出门也这样？

[3-12s] 发现产品
画面：产品摆拍 + 细节特写
口播：直到我发现了这个{name}...
画面：依次展示{len(selling_points)}个卖点
{chr(10).join([f'口播：{i+1}. {s.strip()}' for i, s in enumerate(selling_points[:4])])}

[12-25s] 产品展示
画面：真实使用场景
口播：用了一个月，真的回不去了
画面：对比展示效果

[25-30s] 引导
画面：产品+价格
口播：链接放左下角了，自己看
文字：限时福利 ¥{price}

#好物分享 #{name} #夏日必备"""
    
    else:
        return f"""## {name} — 60s 深度测评脚本

• BGM：舒缓节奏
• 口播风格：专业测评

（完整脚本生成篇幅较长，实际使用时 Codex 会自动展开）
#好物测评 #{name} #良心推荐"""

def generate_xiaohongshu(product):
    """生成小红书种草文案"""
    name = product.get("商品名称", "")
    price = product.get("目标售价", "49.9")
    selling_points = product.get("卖点", "").split("/")
    
    title = f"这个{name}我真的会谢！{selling_points[0] if selling_points else '绝了'}！！"
    
    body = f"""家人们谁懂啊！😭

最近入手了这款{name}，本来没抱太大期望的
结果用了之后真香了！

{chr(10)}{chr(10).join([f'💯 第{i+1}点：{s.strip()}' for i, s in enumerate(selling_points[:5])])}

👗 搭配建议：随便搭都好看！
💰 价格：才¥{price}，还要什么自行车！

真的可以冲！！信我！！

#好物分享 #{name} #平价好物 #良心推荐 #我的宝藏好物
"""
    return {"title": title, "body": body}

def main():
    import argparse
    parser = argparse.ArgumentParser(description="批量内容生成")
    parser.add_argument("--input", default="products.csv", help="商品CSV")
    parser.add_argument("--type", default="all", choices=["all", "image_prompt", "video_script", "xiaohongshu"])
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        input_path = os.path.join(os.path.dirname(__file__), "..", "workspace", "products", args.input)
    
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件，请确认 workspace/products/ 下有 products.csv")
        return
    
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        products = list(reader)
    
    print(f"📦 共 {len(products)} 个商品")
    
    base_dir = os.path.join(os.path.dirname(__file__), "..", "workspace", "content")
    os.makedirs(os.path.join(base_dir, "images", "prompts"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "videos", "scripts"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "xiaohongshu"), exist_ok=True)
    
    for i, product in enumerate(products, 1):
        name = product.get("商品名称", f"商品{i}")
        safe_name = name.replace("/", "_").replace("\\", "_")
        print(f"\n[{i}/{len(products)}] {name}")
        
        if args.type in ("all", "image_prompt"):
            prompts = generate_image_prompt(product)
            filepath = os.path.join(base_dir, "images", "prompts", f"{safe_name}_prompts.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {name} — AI 作图提示词\n\n")
                for style, prompt in prompts.items():
                    f.write(f"## {style}\n```\n{prompt}\n```\n\n")
            print(f"  ✓ 图片提示词 → {filepath}")
        
        if args.type in ("all", "video_script"):
            script = generate_short_video_script(product, 30)
            filepath = os.path.join(base_dir, "videos", "scripts", f"{safe_name}_30s.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(script)
            print(f"  ✓ 视频脚本 → {filepath}")
        
        if args.type in ("all", "xiaohongshu"):
            post = generate_xiaohongshu(product)
            filepath = os.path.join(base_dir, "xiaohongshu", f"{safe_name}.md")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 标题：{post['title']}\n\n{post['body']}")
            print(f"  ✓ 小红书文案 → {filepath}")
    
    print(f"\n✅ 全部完成！输出目录：{base_dir}")

if __name__ == "__main__":
    main()
