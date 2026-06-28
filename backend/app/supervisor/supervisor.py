class Supervisor:
    def __init__(self, handlers: dict):
        self.handlers = handlers

    def execute_task(self, task):
        handler = self.handlers.get(task.intent)
        if not handler:
            return {"error": "unknown intent"}
        return handler.handle(task.data)
