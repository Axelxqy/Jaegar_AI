from backend.modelCore.qwen import QwenModel

class JaegarAgent:
    def __init__(self):
        self.model = QwenModel("models/qwen3.5-9b-mlx") # Call to Load Qwen Model

    def respond(self, message: str) -> str:
        return self.model.generate(message)