from pydantic import BaseModel


class Strategy(BaseModel):
    id: str
    name: str
    tool_priority: list[str] = []
    avoid_tools: list[str] = []
    max_steps: int = 5
    description: str = ""


class StrategyRegistry:
    def __init__(self):
        self.strategies: dict[str, Strategy] = {}
        self.current_strategy_id: str = "default"
        self._register_defaults()

    def _register_defaults(self):
        self.register(Strategy(
            id="default",
            name="Default",
            tool_priority=["product.create", "product.list", "product.get"],
            avoid_tools=[],
            max_steps=5,
            description="balanced planning"
        ))
        self.register(Strategy(
            id="fast_execution",
            name="Fast Execution",
            tool_priority=["product.create", "product.list"],
            avoid_tools=["product.update"],
            max_steps=3,
            description="minimal steps, create + list only"
        ))
        self.register(Strategy(
            id="safe_mode",
            name="Safe Mode",
            tool_priority=["product.list", "product.get"],
            avoid_tools=[],
            max_steps=10,
            description="verify before act, list first"
        ))
        self.register(Strategy(
            id="batch_operation",
            name="Batch Operation",
            tool_priority=["product.create", "product.list"],
            avoid_tools=[],
            max_steps=10,
            description="multiple creates in one plan"
        ))

    def register(self, strategy: Strategy):
        self.strategies[strategy.id] = strategy

    def get(self, strategy_id: str) -> Strategy:
        return self.strategies.get(strategy_id, self.strategies["default"])

    def get_current(self) -> Strategy:
        return self.strategies.get(self.current_strategy_id, self.strategies["default"])

    def switch_to(self, strategy_id: str) -> Strategy:
        if strategy_id in self.strategies:
            self.current_strategy_id = strategy_id
            return self.strategies[strategy_id]
        return self.get_current()

    def suggest_strategy(self, failure_patterns: dict) -> str:
        if not failure_patterns:
            return self.current_strategy_id

        for key, pattern in failure_patterns.items():
            if pattern["count"] >= 3:
                return "safe_mode"

        if len(failure_patterns) >= 3:
            return "safe_mode"

        return self.current_strategy_id

    def list_strategies(self) -> list[dict]:
        return [
            {"id": s.id, "name": s.name, "description": s.description, "current": s.id == self.current_strategy_id}
            for s in self.strategies.values()
        ]
