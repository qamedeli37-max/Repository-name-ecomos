from app.agent.planner import PlannerAgent
from app.agent.critic import CriticAgent
from app.agent.executor import ExecutorAgent
from app.agent.state_manager import StateManager
from app.agent.strategy import StrategyRegistry
from app.agent.meta import MetaStateManager

MAX_REPLANS = 3
MIN_SCORE = 0.7


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools
        self.strategy_registry = StrategyRegistry()
        self.meta_manager = MetaStateManager()
        self.planner = PlannerAgent(strategy_registry=self.strategy_registry)
        self.critic = CriticAgent()
        self.executor = ExecutorAgent(tools)
        self.state_manager = StateManager()

    def run(self, user_input: str):
        goal = self._parse_goal(user_input)
        goal_type = self._detect_goal_type(goal.get("goal", ""))
        state = self.state_manager.create(goal=goal.get("goal", ""), plan=[])
        memory = self.state_manager.get_memory()
        strategy = self.strategy_registry.get_current()
        meta_state = self.meta_manager.get_state()

        replan_count = 0
        last_critic_result = None

        while state.status != "done" and replan_count < MAX_REPLANS:
            plan_data = self.planner.plan(goal, self.tools, memory, strategy, meta_state)
            plans = plan_data.get("plans", [])

            critic_result = self.critic.evaluate(goal, plans, memory, strategy, meta_state)
            last_critic_result = critic_result

            if critic_result.suggested_strategy:
                old_id = self.strategy_registry.current_strategy_id
                new_strategy = self.strategy_registry.switch_to(critic_result.suggested_strategy)
                if old_id != new_strategy.id:
                    strategy = new_strategy
                    plan_data = self.planner.plan(goal, self.tools, memory, strategy, meta_state)
                    plans = plan_data.get("plans", [])
                    critic_result = self.critic.evaluate(goal, plans, memory, strategy, meta_state)
                    last_critic_result = critic_result

            selected_id = critic_result.selected_plan
            selected_plan = critic_result.plan_details.get(selected_id, plans[0])
            state.plan = selected_plan.get("steps", [])
            self.state_manager.save(state)

            exec_result = self.executor.execute_plan(state.plan)

            for step_result in exec_result.steps:
                self.state_manager.append_result(state, step_result)
                if step_result.get("status") == "failed":
                    self.state_manager.record_failure(
                        step=step_result.get("tool", "unknown"),
                        error=step_result.get("error", "unknown"),
                        goal_type=goal_type,
                        context={"execution_id": state.execution_id, "strategy": strategy.id}
                    )

            if exec_result.requires_replan and replan_count < MAX_REPLANS - 1:
                replan_count += 1
                refined = self.planner.refine_plan(goal, self.tools, exec_result.feedback, memory, strategy, meta_state)
                state.plan = []
                self.state_manager.save(state)
            else:
                break

        success = not any(s.get("status") == "failed" for s in state.history)
        self.state_manager.mark_done(state, success)

        score = last_critic_result.score_map.get(selected_id, 0) if last_critic_result else 0
        self.state_manager.record_plan_score(
            plan_id=selected_id,
            plan_steps=state.plan,
            score=score,
            success=success,
            goal_type=goal_type
        )

        self.meta_manager.record_execution(
            goal=state.goal,
            strategy=strategy.id,
            success=success,
            steps_count=len(state.history),
            replans=replan_count,
            score=score
        )

        response = {
            "execution_id": state.execution_id,
            "goal": state.goal,
            "status": state.status,
            "steps": state.history,
            "replans": replan_count,
            "strategy": strategy.id,
            "meta_state": self.meta_manager.get_state().model_dump(),
            "memory_summary": memory.summary()
        }

        if last_critic_result:
            response["critic"] = last_critic_result.to_dict()

        return response

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

    def _detect_goal_type(self, goal: str) -> str:
        goal_lower = goal.lower()
        if "create" in goal_lower or "创建" in goal_lower:
            return "product_create"
        if "update" in goal_lower or "修改" in goal_lower:
            return "product_update"
        if "list" in goal_lower or "show" in goal_lower or "查看" in goal_lower:
            return "product_list"
        return "unknown"
