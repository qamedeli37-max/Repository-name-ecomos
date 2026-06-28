from app.agent.planner import PlannerAgent
from app.agent.critic import CriticAgent
from app.agent.executor import ExecutorAgent
from app.agent.state_manager import StateManager
from app.agent.strategy import StrategyRegistry
from app.agent.profile import ProfileManager
from app.agent.cognition import get_cognition_config
from app.agent.timeline import ExecutionTimeline
from app.agent.context_builder import ContextBuilder
from app.agent.guard import ExecutionGuard
from app.agent.stabilizer import CriticStabilizer
from app.agent.failure_policy import FailurePolicy, FailureAction
from app.services.execution_service import ExecutionService


class Agent:
    def __init__(self, tools: dict):
        self.tools = tools
        self.strategy_registry = StrategyRegistry()
        self.profile_manager = ProfileManager()
        self.planner = PlannerAgent(strategy_registry=self.strategy_registry)
        self.critic = CriticAgent()
        self.executor = ExecutorAgent(tools)
        self.state_manager = StateManager()
        self.execution_service = ExecutionService()
        self.context_builder = ContextBuilder()
        self.guard = ExecutionGuard()
        self.stabilizer = CriticStabilizer()
        self.failure_policy = FailurePolicy()

    def run(self, user_input: str, tenant_id: str = None, debug: bool = False):
        timeline = ExecutionTimeline()
        timeline.start()
        debug_data = {} if debug else None

        goal = self._parse_goal(user_input)
        state = self.state_manager.create(goal=goal.get("goal", ""), plan=[], tenant_id=tenant_id)
        memory = self.state_manager.get_memory(tenant_id)

        profile = self.profile_manager.get_current()
        strategy = self.strategy_registry.get_current()
        cognition_config = get_cognition_config(profile.id)

        ctx = self.context_builder.build(goal, profile, strategy, cognition_config, memory)
        self.guard.reset(cognition_config)
        self.failure_policy.reset()

        if debug:
            debug_data["context"] = ctx.model_dump()
            debug_data["guard"] = self.guard.status()

        self.execution_service.log_start(
            execution_id=state.execution_id,
            goal=state.goal,
            tenant_id=tenant_id,
            strategy=strategy.id,
            profile=profile.id,
            cognition=cognition_config.level
        )
        timeline.record("init")

        replan_count = 0
        last_score = 0
        critic_feedback = None

        while state.status != "done" and replan_count < (cognition_config.max_steps if cognition_config.allow_replan else 0):
            if not self.guard.can_step():
                if debug:
                    debug_data["guard_stop"] = "max_steps exceeded"
                break

            plan_data = self.planner.plan(
                goal, self.tools, memory,
                strategy=strategy, profile=profile,
                cognition_config=cognition_config,
                critic_feedback=critic_feedback
            )
            plans = plan_data.get("plans", [])
            timeline.record("planning")

            if debug:
                debug_data["plans"] = plans

            selected_plan = plans[0] if plans else {"steps": []}
            state.plan = selected_plan.get("steps", [])
            self.state_manager.save(state, tenant_id)

            raw_critic = self.critic.evaluate(goal, state.plan, memory, cognition_config)
            stabilized = self.stabilizer.stabilize(
                raw_critic.score, raw_critic.suggestions,
                state.plan, cognition_config
            )
            timeline.record("critic")
            last_score = stabilized.score

            if debug:
                debug_data["critic"] = stabilized.model_dump()

            if not stabilized.approved and replan_count < (cognition_config.max_steps if cognition_config.allow_replan else 0) - 1:
                replan_count += 1
                high_issues = [i for i in stabilized.issues if i.severity == "high"]
                critic_feedback = {
                    "suggestion": high_issues[0].message if high_issues else "; ".join(stabilized.suggestions),
                    "score": stabilized.score
                }
                state.plan = []
                self.state_manager.save(state, tenant_id)
                timeline.record("replan", metadata={"reason": "critic_rejected"})
                continue

            exec_result = self.executor.execute_plan(state.plan, profile, cognition_config, self.guard)
            timeline.record("execution")

            if debug:
                debug_data["tool_args"] = [{"tool": s.get("tool"), "args": s.get("args", {})} for s in state.plan]
                debug_data["execution_results"] = exec_result.steps

            for step_result in exec_result.steps:
                self.state_manager.append_result(state, step_result, tenant_id)
                self.execution_service.log_step(state.execution_id, step_result)

                if step_result.get("status") == "failed":
                    error_msg = step_result.get("error", "unknown")
                    error_type = self.failure_policy.classify_error(error_msg)
                    action = self.failure_policy.decide(
                        error_type, step_result.get("tool", ""),
                        self.guard._retry_count, self.guard.max_retry
                    )

                    if debug:
                        debug_data.setdefault("failure_actions", []).append({
                            "tool": step_result.get("tool"),
                            "error_type": error_type,
                            "action": action.value
                        })

                    self.state_manager.record_failure(
                        step=step_result.get("tool", "unknown"),
                        error=error_msg,
                        goal_type=ctx.goal_type,
                        context={"execution_id": state.execution_id, "action": action.value},
                        tenant_id=tenant_id
                    )

                    if action == FailureAction.STOP:
                        break
                    elif action == FailureAction.REPLAN:
                        if replan_count < (cognition_config.max_steps if cognition_config.allow_replan else 0) - 1:
                            replan_count += 1
                            critic_feedback = {"suggestion": error_msg, "score": 0}
                            state.plan = []
                            self.state_manager.save(state, tenant_id)
                            timeline.record("replan", metadata={"reason": "failure_policy"})
                            break

            if exec_result.requires_replan and replan_count < (cognition_config.max_steps if cognition_config.allow_replan else 0) - 1:
                replan_count += 1
                critic_feedback = {
                    "suggestion": "; ".join(exec_result.feedback) if exec_result.feedback else "execution failed",
                    "score": 0
                }
                state.plan = []
                self.state_manager.save(state, tenant_id)
                timeline.record("replan", metadata={"reason": "execution_failed"})
            else:
                break

        success = not any(s.get("status") == "failed" for s in state.history)
        self.state_manager.mark_done(state, success, tenant_id)

        self.state_manager.record_plan_score(
            plan_id=selected_plan.get("id", "a"),
            plan_steps=state.plan,
            score=last_score,
            success=success,
            goal_type=ctx.goal_type,
            tenant_id=tenant_id
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
            score=last_score,
            replans=replan_count
        )
        timeline.record("complete")

        response = {
            "execution_id": state.execution_id,
            "goal": state.goal,
            "status": state.status,
            "steps": state.history,
            "replans": replan_count,
            "score": last_score,
            "strategy": strategy.id,
            "profile": profile.id,
            "cognition": cognition_config.level,
            "guard": self.guard.status(),
            "timeline": timeline.get_summary(),
            "tenant_id": tenant_id
        }

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
        return {"goal": user_input, "constraints": [], "context": {}}
