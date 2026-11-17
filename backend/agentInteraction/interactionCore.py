from backend.agentCore.core import JaegarAgent

class InteractionCore:
    """
    Coordinates user interactions before passing to Agent Core
    """

    def __init__(self, agent: JaegarAgent):
        self.agent = agent

    def process_message(self, message:str) -> str:
        """
        Validates and process a text interaction
        """

        if not isinstance(message, str):
            raise ValueError("Message must be a string")

        message = message.strip()

        if not message:
            raise ValueError("Message cannot be empty")

        response = self.agent.respond(message)

        return response