import json
import os
import re
from dotenv import load_dotenv

load_dotenv()


class PlannerAgent:
    def __init__(self, strategy_registry=None):
        self._init_llm()
        self.strategy_registry = strategy_registry

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def plan(self, goal: dict, tools: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None) -> dict:
        if self.client:
            return self._llm_plan(goal, tools, memory, strategy, meta_state, profile, cognition_config)
        return {"plans": [{"id": "a", "steps": self._rule_plan(goal, memory, strategy, meta_state, profile, cognition_config)}]}

    def refine_plan(self, goal: dict, tools: dict, feedback: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None) -> dict:
        if self.client:
            return self._llm_refine(goal, tools, feedback, memory, strategy, meta_state, profile, cognition_config)
        return {"plans": [{"id": "a", "steps": self._rule_refine(goal, feedback, memory, strategy, meta_state, profile, cognition_config)}]}

    def _llm_plan(self, goal: dict, tools: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None):
        tool_list = "\n".join(tools.keys())
        memory_context = self._build_memory_context(goal, memory)
        strategy_context = self._build_strategy_context(strategy)
        meta_context = self._build_meta_context(meta_state)
        profile_context = self._build_profile_context(profile)
        cog_context = self._build_cognition_context(cognition_config)

        reasoning_note = ""
        if cognition_config:
            if cognition_config.level == "shallow":
                reasoning_note = "Keep reasoning minimal. Single step plan only."
            elif cognition_config.level == "deep":
                reasoning_note = "Analyze thoroughly. Multi-step plan with fallback steps."
            else:
                reasoning_note = "Balance speed and thoroughness. 2-5 steps."

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner. Generate 2-3 different plans.

{reasoning_note}
Max steps allowed: {cognition_config.max_steps if cognition_config else 5}.
Follow the active profile's planner style.
Use meta-state insights to improve planning.
Follow the active strategy constraints.
CRITICAL: Avoid all known failure patterns.

Return ONLY valid JSON:
{{
    "plans": [
        {{
            "id": "a",
            "steps": [{{"tool": "tool.name", "args": {{}}}}]
        }}
    ]
}}

Available tools:
{tool_list}

{profile_context}
{cog_context}
{strategy_context}
{meta_context}
{memory_context}"""
                },
                {"role": "user", "content": json.dumps(goal)}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _llm_refine(self, goal: dict, tools: dict, feedback: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None):
        tool_list = "\n".join(tools.keys())
        memory_context = self._build_memory_context(goal, memory)
        strategy_context = self._build_strategy_context(strategy)
        meta_context = self._build_meta_context(meta_state)
        profile_context = self._build_profile_context(profile)
        cog_context = self._build_cognition_context(cognition_config)

        reasoning_note = ""
        if cognition_config:
            if cognition_config.level == "shallow":
                reasoning_note = "Minimal reasoning. Quick fix."
            elif cognition_config.level == "deep":
                reasoning_note = "Deep analysis. Understand root cause before fixing."
            else:
                reasoning_note = "Balanced approach to fixing."

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner. A previous plan failed.

{reasoning_note}
Max steps: {cognition_config.max_steps if cognition_config else 5}.
Follow the active profile's planner style.
Use meta-state insights to improve planning.
Follow the active strategy constraints.
CRITICAL: Avoid all known failure patterns.
Generate 2-3 NEW plans that avoid the error.

Return ONLY valid JSON:
{{
    "plans": [
        {{
            "id": "a",
            "steps": [{{"tool": "tool.name", "args": {{}}}}]
        }}
    ]
}}

Available tools:
{tool_list}

{profile_context}
{cog_context}
{strategy_context}
{meta_context}
{memory_context}"""
                },
                {
                    "role": "user",
                    "content": f"Goal: {json.dumps(goal)}\nFailed step: {json.dumps(feedback.get('failed_step'))}\nError: {feedback.get('error')}"
                }
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    def _build_memory_context(self, goal: dict, memory) -> str:
        if not memory:
            return ""
        goal_text = goal.get("goal", "")
        parts = []

        successful = memory.get_successful_plans(goal_text)
        if successful:
            parts.append(f"Past successful plans: {json.dumps(successful[:2])}")

        failed = memory.get_failed_patterns(goal_text)
        if failed:
            parts.append(f"Past failed steps to avoid: {json.dumps(failed[:2])}")

        high_score = memory.get_high_score_plans(min_score=0.8)
        if high_score:
            patterns = [{"tools": [s["tool"] for s in r.plan_steps], "score": r.score} for r in high_score[:3]]
            parts.append(f"High-score plan patterns to emulate: {json.dumps(patterns)}")

        failure_patterns = memory.get_failure_patterns()
        if failure_patterns:
            avoid_list = [{"step": v["step"], "error": v["error_type"], "count": v["count"]} for v in failure_patterns.values()]
            parts.append(f"AVOID these failure patterns: {json.dumps(avoid_list)}")

        return "\n".join(parts) if parts else ""

    def _build_strategy_context(self, strategy) -> str:
        if not strategy:
            return ""
        parts = [f"Active strategy: {strategy.name}"]
        if strategy.tool_priority:
            parts.append(f"Prioritize tools: {', '.join(strategy.tool_priority)}")
        if strategy.avoid_tools:
            parts.append(f"Avoid tools: {', '.join(strategy.avoid_tools)}")
        parts.append(f"Max steps: {strategy.max_steps}")
        return "\n".join(parts)

    def _build_meta_context(self, meta_state) -> str:
        if not meta_state:
            return ""
        parts = []

        perf = meta_state.performance
        parts.append(f"System performance: success_rate={perf.success_rate:.2f}, avg_steps={perf.avg_steps:.1f}")

        if perf.avg_replans > 1:
            parts.append("High replan rate detected - generate more robust plans")

        if perf.avg_score < 0.7:
            parts.append("Low average score - focus on high-quality plans")

        if len(meta_state.strategy_history) > 1:
            parts.append(f"Strategy evolution: {' -> '.join(meta_state.strategy_history)}")

        return "\n".join(parts) if parts else ""

    def _build_profile_context(self, profile) -> str:
        if not profile:
            return ""
        parts = [f"Active profile: {profile.name}"]
        parts.append(f"Planner style: {profile.planner_style}")
        parts.append(f"Critic threshold: {profile.critic_threshold}")
        parts.append(f"Max replans: {profile.max_replans}")
        if profile.planner_style == "minimal_steps":
            parts.append("Generate concise plans with fewest steps possible")
        elif profile.planner_style == "thorough":
            parts.append("Generate comprehensive plans, include verification steps")
        return "\n".join(parts)

    def _build_cognition_context(self, cognition_config) -> str:
        if not cognition_config:
            return ""
        parts = [f"Cognition: level={cognition_config.level}"]
        parts.append(f"Max steps: {cognition_config.max_steps}")
        parts.append(f"Allow replan: {cognition_config.allow_replan}")
        parts.append(f"Verification: {cognition_config.verification_level}")
        return "\n".join(parts)

    def _rule_plan(self, goal: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None):
        text = goal.get("goal", "").lower()
        steps = []
        avoid_tools = set()
        priority_tools = []

        if strategy:
            avoid_tools = set(strategy.avoid_tools)
            priority_tools = strategy.tool_priority

        if meta_state and meta_state.performance.avg_replans > 1.5:
            if "product.create" not in avoid_tools:
                steps.append({"tool": "product.list", "args": {}})

        if memory:
            failure_patterns = memory.get_failure_patterns()
            high_score = memory.get_high_score_plans(min_score=0.8)

            if high_score:
                best = high_score[0]
                return [dict(s) for s in best.plan_steps]

            if failure_patterns:
                for key, pattern in failure_patterns.items():
                    if pattern["count"] >= 2:
                        avoid_tools.add(pattern["step"])

        if profile and profile.planner_style == "minimal_steps":
            if "create" in text or "创建" in text:
                if "product.create" not in avoid_tools:
                    steps.append({"tool": "product.create", "args": self._parse_product_create(text)})
            if "list" in text or "show" in text or "查看" in text:
                if "product.list" not in avoid_tools:
                    steps.append({"tool": "product.list", "args": {}})
            if not steps:
                if "product.list" not in avoid_tools:
                    steps.append({"tool": "product.list", "args": {}})
            return steps

        if "create" in text or "创建" in text:
            if "product.create" not in avoid_tools:
                steps.append({"tool": "product.create", "args": self._parse_product_create(text)})
        if "update" in text or "修改" in text:
            if "product.update" not in avoid_tools:
                steps.append({"tool": "product.update", "args": self._parse_product_update(text)})
        if "list" in text or "show all" in text or "查看所有" in text:
            if "product.list" not in avoid_tools:
                steps.append({"tool": "product.list", "args": {}})
        elif "get" in text or "show" in text or "查看" in text:
            if "product.get" not in avoid_tools:
                steps.append({"tool": "product.get", "args": {}})

        if not steps:
            if "product.list" not in avoid_tools:
                steps.append({"tool": "product.list", "args": {}})

        if priority_tools and not steps:
            steps.append({"tool": priority_tools[0], "args": {}})

        return steps

    def _rule_refine(self, goal: dict, feedback: dict, memory=None, strategy=None, meta_state=None, profile=None, cognition_config=None):
        failed_step = feedback.get("failed_step", {})
        tool_name = failed_step.get("tool", "")
        if tool_name == "product.create":
            return [{"tool": "product.list", "args": {}}]
        return self._rule_plan(goal, memory, strategy, meta_state, profile, cognition_config)

    def _parse_product_create(self, text: str):
        price_match = re.search(r'(\d+(?:\.\d+)?)', text)
        price = float(price_match.group(1)) if price_match else 0
        cleaned = re.sub(r'create\s+(a\s+)?product\s*', '', text, flags=re.IGNORECASE)
        cleaned = re.sub(r'帮我创建', '', cleaned)
        cleaned = re.sub(r'\d+(?:\.\d+)?', '', cleaned).strip()
        title = cleaned if cleaned else "Untitled"
        return {"title": title, "price": price}

    def _parse_product_update(self, text: str):
        price_match = re.search(r'(\d+(?:\.\d+)?)', text)
        return {"id": "", "price": float(price_match.group(1)) if price_match else 0}
