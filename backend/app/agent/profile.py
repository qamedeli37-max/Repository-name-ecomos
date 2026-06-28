from pydantic import BaseModel


class BehavioralProfile(BaseModel):
    id: str
    name: str
    planner_style: str  # minimal_steps, thorough, adaptive
    critic_threshold: float  # 0.0-1.0, minimum score to approve
    max_replans: int
    retry_enabled: bool
    auto_fix: bool
    description: str = ""


class ProfileManager:
    def __init__(self):
        self.profiles: dict[str, BehavioralProfile] = {}
        self.current_profile_id: str = "balanced"
        self.profile_history: list[str] = ["balanced"]
        self._register_defaults()

    def _register_defaults(self):
        self.register(BehavioralProfile(
            id="balanced",
            name="Balanced",
            planner_style="adaptive",
            critic_threshold=0.7,
            max_replans=3,
            retry_enabled=True,
            auto_fix=True,
            description="default balanced profile"
        ))
        self.register(BehavioralProfile(
            id="efficient_executor",
            name="Efficient Executor",
            planner_style="minimal_steps",
            critic_threshold=0.8,
            max_replans=2,
            retry_enabled=True,
            auto_fix=False,
            description="fast execution, minimal steps, higher quality bar"
        ))
        self.register(BehavioralProfile(
            id="safe_executor",
            name="Safe Executor",
            planner_style="thorough",
            critic_threshold=0.6,
            max_replans=5,
            retry_enabled=True,
            auto_fix=True,
            description="conservative, more replans, always retry and fix"
        ))
        self.register(BehavioralProfile(
            id="aggressive",
            name="Aggressive",
            planner_style="minimal_steps",
            critic_threshold=0.5,
            max_replans=1,
            retry_enabled=False,
            auto_fix=False,
            description="minimal retries, accept lower scores"
        ))
        self.register(BehavioralProfile(
            id="learning",
            name="Learning",
            planner_style="adaptive",
            critic_threshold=0.7,
            max_replans=4,
            retry_enabled=True,
            auto_fix=True,
            description="extra replans for learning from failures"
        ))

    def register(self, profile: BehavioralProfile):
        self.profiles[profile.id] = profile

    def get(self, profile_id: str) -> BehavioralProfile:
        return self.profiles.get(profile_id, self.profiles["balanced"])

    def get_current(self) -> BehavioralProfile:
        return self.profiles.get(self.current_profile_id, self.profiles["balanced"])

    def switch_to(self, profile_id: str) -> BehavioralProfile:
        if profile_id in self.profiles:
            self.current_profile_id = profile_id
            if profile_id not in self.profile_history:
                self.profile_history.append(profile_id)
            return self.profiles[profile_id]
        return self.get_current()

    def suggest_profile(self, meta_state=None, failure_patterns: dict = None) -> str:
        if meta_state:
            perf = meta_state.performance

            if perf.total_executions >= 3:
                if perf.success_rate < 0.6:
                    return "safe_executor"
                if perf.success_rate > 0.95 and perf.avg_steps <= 2:
                    return "efficient_executor"
                if perf.avg_replans > 2:
                    return "learning"

        if failure_patterns:
            if len(failure_patterns) >= 3:
                return "safe_executor"

        return self.current_profile_id

    def list_profiles(self) -> list[dict]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "current": p.id == self.current_profile_id
            }
            for p in self.profiles.values()
        ]
