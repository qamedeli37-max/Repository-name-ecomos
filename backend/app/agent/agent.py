import json
import os
import re
from uuid import uuid4
from dotenv import load_dotenv
from app.agent.state import ExecutionState, StateStore

load_dotenv()

MAX_RETRY = 2

store = StateStore()


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools
        self._init_llm()

    def _init_llm(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

    def run(self, user_input: str):
        execution_id = str(uuid4())
        goal = self._parse_goal(user_input)

        if self.client:
            plan_data = self._llm_plan(goal)
        else:
            plan_data = {"plan": self._rule_plan(goal)}

        state = ExecutionState(
            execution_id=execution_id,
            goal=goal.get("goal", ""),
            plan=plan_data.get("plan", []),
            status="running",
            current_step=0,
            history=[]
        )
        store.save(state)
        return self.execute_loop(state)

    def resume(self, execution_id: str):
        state = store.get(execution_id)
        if not state:
            return {"error": "execution not found"}
        if state.status == "done":
            return {"error": "execution already done"}
        state.status = "running"
        return self.execute_loop(state)

    def execute_loop(self, state: ExecutionState):
        while state.status != "done" and state.current_step < len(state.plan):
            step = state.plan[state.current_step]
            tool = self.tools.get(step.get("tool"))

            if not tool:
                state.history.append({
                    "tool": step.get("tool"),
                    "status": "failed",
                    "error": f"tool not found: {step.get('tool')}"
                })
                state.current_step += 1
                continue

            attempt = 0
            success = False
            last_error = None

            while attempt < MAX_RETRY and not success:
                try:
                    result = tool.execute(step.get("args", {}))
                    success = True
                except Exception as e:
                    attempt += 1
                    last_error = str(e)
                    if attempt < MAX_RETRY and self.client:
                        step = self.fix_step(step, last_error)

            if success:
                state.history.append({
                    "tool": step.get("tool"),
                    "status": "success",
                    "result": result
                })
            else:
                state.history.append({
                    "tool": step.get("tool"),
                    "status": "failed",
                    "error": last_error
                })

            state.current_step += 1
            store.save(state)

        state.status = "done"
        store.save(state)

        return {
            "execution_id": state.execution_id,
            "goal": state.goal,
            "status": state.status,
            "steps": state.history
        }

    # ========== LLM Fix ==========

    def fix_step(self, step: dict, error: str):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """This tool call failed. Fix the arguments.
Return ONLY valid JSON with corrected args."""
                },
                {
                    "role": "user",
                    "content": f"Step: {json.dumps(step)}\nError: {error}"
                }
            ]
        )
        content = response.choices[0].message.content
        fixed = json.loads(content)
        step["args"] = fixed.get("args", step.get("args", {}))
        return step

    # ========== LLM Planner ==========

    def _llm_plan(self, goal: dict):
        tool_list = "\n".join(self.tools.keys())
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a task planner.

Given a goal, create a plan with steps.

Return ONLY valid JSON:
{{
    "goal": "the goal description",
    "plan": [
        {{
            "tool": "tool.name",
            "args": {{}}
        }}
    ]
}}

Available tools:
{tool_list}"""
                },
                {"role": "user", "content": json.dumps(goal)}
            ]
        )
        content = response.choices[0].message.content
        return json.loads(content)

    # ========== Rule Mode (fallback) ==========

    def _rule_plan(self, goal: dict):
        text = goal.get("goal", "").lower()
        steps = []

        if "create" in text or "创建" in text:
            steps.append({"tool": "product.create", "args": self._parse_product_create(text)})

        if "update" in text or "修改" in text:
            steps.append({"tool": "product.update", "args": self._parse_product_update(text)})

        if "list" in text or "show all" in text or "查看所有" in text:
            steps.append({"tool": "product.list", "args": {}})
        elif "get" in text or "show" in text or "查看" in text:
            steps.append({"tool": "product.get", "args": {}})

        if not steps:
            steps.append({"tool": "product.list", "args": {}})

        return steps

    def _parse_goal(self, user_input):
        if isinstance(user_input, dict):
            return {
                "goal": user_input.get("goal", ""),
                "constraints": user_input.get("constraints", []),
                "context": user_input.get("context", {})
            }
        return {
            "goal": user_input,
            "constraints": [],
            "context": {}
        }

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
