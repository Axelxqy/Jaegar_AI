from abc import ABC, abstractmethod

class JaegarInterface(ABC):
    @abstractmethod
    def generate(self, messages: list[dict[str, str]]) -> str:
        pass