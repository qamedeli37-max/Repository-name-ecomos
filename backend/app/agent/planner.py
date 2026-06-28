import json
import os
from dotenv import load_dotenv

load_dotenv()


class PlannerAgent:
    def __init__(self, strategy_registry=None):
        self.strategy_registry = strategy_registry
        self._init_llm()

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def plan(self, goal: dict, tools: dict, memory=None, strategy=None, profile=None, cognition_config=None, critic_feedback=None) -> dict:
        reasoning = self._get_reasoning(cognition_config)

        if critic_feedback:
            goal = self._apply_feedback(goal, critic_feedback)

        if self.client:
            return self._llm_plan(goal, tools, memory, strategy, profile, cognition_config, reasoning)
        return self._rule_plan(goal, tools, memory, strategy, profile, cognition_config, reasoning)

    def refine_plan(self, goal: dict, tools: dict, feedback: str, memory=None, strategy=None, profile=None, cognition_config=None) -> dict:
        return self.plan(goal, tools, memory, strategy, profile, cognition_config, critic_feedback={"suggestion": feedback})

    def _apply_feedback(self, goal: dict, feedback: dict) -> dict:
        suggestion = feedback.get("suggestion", "")
        if suggestion:
            constraints = goal.get("constraints", [])
            constraints.append(f"avoid: {suggestion}")
            goal = {**goal, "constraints": constraints}
        return goal

    def _get_reasoning(self, cognition_config) -> str:
        if not cognition_config:
            return "balanced planning"
        if cognition_config.level == "shallow":
            return "minimal reasoning"
        if cognition_config.level == "deep":
            return "thorough reasoning with fallbacks"
        return "balanced planning"

    def _llm_plan(self, goal: dict, tools: dict, memory=None, strategy=None, profile=None, cognition_config=None, reasoning=""):
        tools_schema = json.dumps([t.to_schema() for t in tools.values()], indent=2)
        memory_context = self._build_memory_context(goal, memory)
        constraints = self._build_constraints(strategy, profile, cognition_config)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a Planner. Create a step-by-step plan.

Reasoning: {reasoning}
{constraints}

Return ONLY valid JSON:
{{
    "plans": [
        {{
            "id": "a",
            "steps": [{{"tool": "tool.name", "args": {{}}}}]
        }}
    ]
}}
{memory_context}"""
                },
                {"role": "user", "content": f"Goal: {json.dumps(goal)}\nTools: {tools_schema}"}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _rule_plan(self, goal: dict, tools: dict, memory=None, strategy=None, profile=None, cognition_config=None, reasoning=""):
        goal_text = goal.get("goal", "").lower()
        plan_a = []
        plan_b = []
        plan_c = []

        avoid_tools = set()
        if strategy:
            avoid_tools = set(strategy.avoid_tools or [])
            tool_priority = strategy.tool_priority or []
        else:
            tool_priority = []

        high_score_tools = set()
        if memory:
            for record in memory.get_high_score_plans(min_score=0.8):
                for step in record.plan_steps:
                    high_score_tools.add(step.get("tool", ""))

        max_steps = 10
        if cognition_config:
            max_steps = cognition_config.max_steps

        price = None
        title = goal_text
        for part in goal_text.split():
            try:
                price = float(part)
                title = title.replace(part, "").strip()
            except ValueError:
                continue

        if "create" in goal_text or "创建" in goal_text:
            clean_title = title.replace("create", "").replace("创建", "").strip()
            if not clean_title:
                clean_title = "new product"
            args = {"title": clean_title}
            if price:
                args["price"] = price
            plan_a = [{"tool": "product.create", "args": args}]
            plan_b = [{"tool": "product.create", "args": {**args, "title": f"{clean_title} v2"}}]

        elif "update" in goal_text or "修改" in goal_text:
            plan_a = [{"tool": "product.update", "args": {"product_id": "latest", "updates": {"title": "updated"}}}]
            plan_b = [{"tool": "product.list", "args": {}}, {"tool": "product.update", "args": {"product_id": "first", "updates": {"title": "updated"}}}]

        elif "list" in goal_text or "show" in goal_text or "查看" in goal_text:
            plan_a = [{"tool": "product.list", "args": {}}]
            plan_b = [{"tool": "product.list", "args": {"limit": 10}}]

        else:
            plan_a = [{"tool": "product.list", "args": {}}]

        if len(plan_a) > max_steps:
            plan_a = plan_a[:max_steps]

        if not plan_b:
            plan_b = list(reversed(plan_a))

        if not plan_c:
            plan_c = list(plan_a)

        plans = [
            {"id": "a", "steps": plan_a},
            {"id": "b", "steps": plan_b},
            {"id": "c", "steps": plan_c}
        ]

        return {"plans": plans}

    def _build_constraints(self, strategy, profile, cognition_config) -> str:
        parts = []
        if strategy:
            parts.append(f"Strategy: {strategy.name} (max {strategy.max_steps} steps)")
            if strategy.avoid_tools:
                parts.append(f"Avoid: {', '.join(strategy.avoid_tools)}")
        if profile:
            parts.append(f"Profile: {profile.name} (style: {profile.planner_style})")
        if cognition_config:
            parts.append(f"Cognition: {cognition_config.level} (max {cognition_config.max_steps} steps)")
        return "\n".join(parts) if parts else ""

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        goal_text = goal.get("goal", "")
        parts = []
        failed = memory.get_failed_patterns(goal_text)
        if failed:
            parts.append(f"Past failures: {json.dumps(failed[:3])}")
        high_score = memory.get_high_score_plans(min_score=0.8)
        if high_score:
            patterns = [{"tools": [s["tool"] for s in r.plan_steps], "score": r.score} for r in high_score[:3]]
            parts.append(f"High-score patterns: {json.dumps(patterns)}")
        return "\nMemory:\n" + "\n".join(parts) if parts else ""
