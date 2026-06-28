from abc import ABC, abstractmethod


class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def execute(self, data: dict): ...

    def to_schema(self) -> dict:
        return {"name": self.name, "description": self.__doc__ or ""}
