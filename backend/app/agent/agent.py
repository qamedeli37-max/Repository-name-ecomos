from app.agent.planner import PlannerAgent
from app.agent.executor import ExecutorAgent
from app.agent.state_manager import StateManager


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent(tools)
        self.state_manager = StateManager()

    def run(self, user_input: str):
        goal = self._parse_goal(user_input)
        plan_data = self.planner.plan(goal, self.tools)
        state = self.state_manager.create(
            goal=goal.get("goal", ""),
            plan=plan_data.get("plan", [])
        )
        return self.execute_loop(state)

    def resume(self, execution_id: str):
        state = self.state_manager.get(execution_id)
        if not state:
            return {"error": "execution not found"}
        if state.status == "done":
            return {"error": "execution already done"}
        state.status = "running"
        return self.execute_loop(state)

    def execute_loop(self, state):
        while state.status != "done" and state.current_step < len(state.plan):
            step = state.plan[state.current_step]
            result = self.executor.execute_step(step)
            self.state_manager.append_result(state, result)

        self.state_manager.mark_done(state)

        return {
            "execution_id": state.execution_id,
            "goal": state.goal,
            "status": state.status,
            "steps": state.history
        }

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
