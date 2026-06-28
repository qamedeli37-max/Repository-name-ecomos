from app.tools.registry import ToolRegistry


class Supervisor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_task(self, task):
        tool = self.registry.get(task.intent)
        if not tool:
            return {"error": f"unknown intent: {task.intent}"}
        return tool.execute(task.data)
