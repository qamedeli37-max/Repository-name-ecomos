import os
from openai import OpenAI

class EcommerceAutomationAgent:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        print("Codex 电商自动化 Agent 已启动。当前角色：电商自动化工程师。")

    def analyze_and_generate(self, product_data: dict) -> dict:
        print(f"\n[1. 数据输入] 正在读取商品数据: {product_data['product_name']}...")
        
        prompt = f"""
你现在是一位专业的电商自动化工程师（Codex）。请根据以下输入的数据，进行卖点提炼与差异化打法分析，并自动生成商品标题及主图文案。

【数据输入】
- 商品名称: {product_data['product_name']}
- 基础属性/材质: {product_data['attributes']}
- 核心痛点/市场趋势: {product_data['market_trends']}
- 竞品定价与缺点: {product_data['competitor_info']}

请严格按照以下 JSON 格式输出分析与生成的内容，不要包含任何常规解释或 Markdown 代码块标记：
{{
    "ai_analysis": {{
        "core_selling_points": ["卖点1", "卖点2", "卖点3"],
        "differentiation_strategy": "针对竞品缺点的差异化打法建议"
    }},
    "content_generation": {{
        "seo_optimized_title": "高点击率、符合SEO的商品标题",
        "main_image_copywriting": ["主图文案1(强利益点)", "主图文案2(场景化)", "主图文案3(解决痛点)"]
    }}
}}
"""
        print("[2. ChatGPT 分析 & 3. 内容生成] 正在解析卖点并批量生产素材描述...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是一个严谨的电商自动化执行中台，只输出标准JSON。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"自动化流程中断: {e}")
            return {}

if __name__ == "__main__":
    API_KEY = "sk-7e6b69676b66459e9435416f66804c79"
    
    agent = EcommerceAutomationAgent(api_key=API_KEY)
    
    mock_input_data = {
        "product_name": "便携式无线多功能吸尘器",
        "attributes": "吸力 12000Pa，重量 450g，续航 40分钟，Type-C 快充",
        "market_trends": "独居青年增加，车载/桌面清洁需求大；注重颜值和收纳便利性",
        "competitor_info": "竞品A售价199元，普遍被差评噪音太大、吸车缝死角吸不干净"
    }
    
    automation_result = agent.analyze_and_generate(mock_input_data)
    
    print("\n[4. 执行落地] Agent 自动化生成报告如下：")
    print("="*60)
    import pprint
    pprint.pprint(automation_result)
    print("="*60)
    print("\n[5. 人工决策] 请审核以上结果。确认无误后，中台可接入下阶段自动上架或投流系统。")
