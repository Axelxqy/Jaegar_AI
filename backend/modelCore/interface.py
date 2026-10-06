from abc import ABC, abstractmethod

class JaegarInterface(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass