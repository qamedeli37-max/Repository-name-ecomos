from app.agent.planner import PlannerAgent
from app.agent.critic import CriticAgent
from app.agent.executor import ExecutorAgent
from app.agent.state_manager import StateManager
from app.agent.strategy import StrategyRegistry
from app.agent.meta import MetaStateManager
from app.agent.profile import ProfileManager
from app.agent.cognition import get_cognition_config
from app.agent.timeline import ExecutionTimeline
from app.services.execution_service import ExecutionService

MAX_REPLANS_BASE = 3
MIN_SCORE = 0.7


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools
        self.strategy_registry = StrategyRegistry()
        self.meta_manager = MetaStateManager()
        self.profile_manager = ProfileManager()
        self.planner = PlannerAgent(strategy_registry=self.strategy_registry)
        self.critic = CriticAgent()
        self.executor = ExecutorAgent(tools)
        self.state_manager = StateManager()
        self.execution_service = ExecutionService()

    def run(self, user_input: str, tenant_id: str = None, debug: bool = False):
        timeline = ExecutionTimeline()
        timeline.start()
        debug_data = {} if debug else None

        goal = self._parse_goal(user_input)
        goal_type = self._detect_goal_type(goal.get("goal", ""))
        state = self.state_manager.create(goal=goal.get("goal", ""), plan=[], tenant_id=tenant_id)
        memory = self.state_manager.get_memory(tenant_id)
        strategy = self.strategy_registry.get_current()
        profile = self.profile_manager.get_current()
        cognition_config = get_cognition_config(profile.id)
        meta_state = self.meta_manager.get_state()

        if debug:
            debug_data["input"] = {"goal": goal, "tenant_id": tenant_id}
            debug_data["strategy"] = strategy.id
            debug_data["profile"] = profile.id
            debug_data["cognition"] = cognition_config.model_dump()

        self.execution_service.log_start(
            execution_id=state.execution_id,
            goal=state.goal,
            tenant_id=tenant_id,
            strategy=strategy.id,
            profile=profile.id,
            cognition=cognition_config.level
        )

        timeline.record("init", metadata={"goal": state.goal})

        max_replans = profile.max_replans if cognition_config.allow_replan else 0
        replan_count = 0
        last_critic_result = None

        while state.status != "done" and replan_count < max_replans:
            plan_data = self.planner.plan(goal, self.tools, memory, strategy, meta_state, profile, cognition_config)
            timeline.record("planning", metadata={"plans_count": len(plan_data.get("plans", []))})

            plans = plan_data.get("plans", [])

            if debug:
                debug_data["plans"] = plans

            critic_result = self.critic.evaluate(goal, plans, memory, strategy, meta_state, profile, cognition_config)
            timeline.record("critic", metadata={"selected": critic_result.selected_plan, "scores": critic_result.score_map})

            last_critic_result = critic_result

            if debug:
                debug_data["critic"] = {
                    "selected_plan": critic_result.selected_plan,
                    "score_map": critic_result.score_map,
                    "suggestions": critic_result.suggestions,
                    "meta_analysis": critic_result.meta_analysis
                }

            if critic_result.suggested_strategy:
                old_id = self.strategy_registry.current_strategy_id
                new_strategy = self.strategy_registry.switch_to(critic_result.suggested_strategy)
                if old_id != new_strategy.id:
                    strategy = new_strategy

            if critic_result.suggested_profile:
                old_pid = self.profile_manager.current_profile_id
                new_profile = self.profile_manager.switch_to(critic_result.suggested_profile)
                if old_pid != new_profile.id:
                    profile = new_profile
                    cognition_config = get_cognition_config(profile.id)
                    max_replans = profile.max_replans if cognition_config.allow_replan else 0

            if critic_result.suggested_strategy or critic_result.suggested_profile:
                plan_data = self.planner.plan(goal, self.tools, memory, strategy, meta_state, profile, cognition_config)
                plans = plan_data.get("plans", [])
                critic_result = self.critic.evaluate(goal, plans, memory, strategy, meta_state, profile, cognition_config)
                last_critic_result = critic_result
                timeline.record("replan", metadata={"reason": "critic_suggested_switch"})

            selected_id = critic_result.selected_plan
            selected_plan = critic_result.plan_details.get(selected_id, plans[0])
            state.plan = selected_plan.get("steps", [])
            self.state_manager.save(state, tenant_id)

            exec_result = self.executor.execute_plan(state.plan, profile, cognition_config)
            timeline.record("execution", metadata={"steps_count": len(exec_result.steps)})

            if debug:
                debug_data["tool_args"] = [{"tool": s.get("tool"), "args": s.get("args", {})} for s in state.plan]
                debug_data["execution_results"] = exec_result.steps

            for step_result in exec_result.steps:
                self.state_manager.append_result(state, step_result, tenant_id)
                self.execution_service.log_step(state.execution_id, step_result)
                if step_result.get("status") == "failed":
                    self.state_manager.record_failure(
                        step=step_result.get("tool", "unknown"),
                        error=step_result.get("error", "unknown"),
                        goal_type=goal_type,
                        context={"execution_id": state.execution_id, "strategy": strategy.id, "profile": profile.id, "cognition": cognition_config.level},
                        tenant_id=tenant_id
                    )

            if exec_result.requires_replan and replan_count < max_replans - 1:
                replan_count += 1
                refined = self.planner.refine_plan(goal, self.tools, exec_result.feedback, memory, strategy, meta_state, profile, cognition_config)
                state.plan = []
                self.state_manager.save(state, tenant_id)
            else:
                break

        success = not any(s.get("status") == "failed" for s in state.history)
        self.state_manager.mark_done(state, success, tenant_id)

        score = last_critic_result.score_map.get(selected_id, 0) if last_critic_result else 0
        self.state_manager.record_plan_score(
            plan_id=selected_id,
            plan_steps=state.plan,
            score=score,
            success=success,
            goal_type=goal_type,
            tenant_id=tenant_id
        )

        self.meta_manager.record_execution(
            goal=state.goal,
            strategy=strategy.id,
            success=success,
            steps_count=len(state.history),
            replans=replan_count,
            score=score
        )

        error_data = None
        if not success:
            failed_step = next((s for s in state.history if s.get("status") == "failed"), None)
            if failed_step:
                error_data = {"type": "tool_error", "message": failed_step.get("error", "unknown")}

        self.execution_service.log_complete(
            execution_id=state.execution_id,
            status="success" if success else "failed",
            result=str(state.history[-1].get("result")) if state.history else None,
            error=error_data,
            score=score,
            replans=replan_count
        )

        timeline.record("complete", metadata={"status": "success" if success else "failed"})

        response = {
            "execution_id": state.execution_id,
            "goal": state.goal,
            "status": state.status,
            "steps": state.history,
            "replans": replan_count,
            "strategy": strategy.id,
            "profile": profile.id,
            "cognition": {
                "level": cognition_config.level,
                "max_steps": cognition_config.max_steps,
                "allow_replan": cognition_config.allow_replan,
                "verification_level": cognition_config.verification_level
            },
            "timeline": timeline.get_summary(),
            "meta_state": self.meta_manager.get_state().model_dump(),
            "memory_summary": memory.summary(),
            "tenant_id": tenant_id
        }

        if last_critic_result:
            response["critic"] = last_critic_result.to_dict()

        if debug:
            response["debug"] = debug_data

        return response

    def resume(self, execution_id: str, tenant_id: str = None):
        state = self.state_manager.get(execution_id, tenant_id)
        if not state:
            return {"error": "execution not found"}
        if state.status == "done":
            return {"error": "execution already done"}
        state.status = "running"
        self.execution_service.log_complete(execution_id=execution_id, status="running")
        return self.execute_loop(state, tenant_id)

    def execute_loop(self, state, tenant_id: str = None):
        while state.status != "done" and state.current_step < len(state.plan):
            step = state.plan[state.current_step]
            result = self.executor.execute_step(step)
            self.state_manager.append_result(state, result, tenant_id)
            self.execution_service.log_step(state.execution_id, result)

        self.state_manager.mark_done(state, True, tenant_id)
        self.execution_service.log_complete(
            execution_id=state.execution_id,
            status="success",
            result=str(state.history[-1].get("result")) if state.history else None
        )

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
