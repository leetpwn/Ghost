# Handles user requests and decides how Ghost should respond.

class GhostAgent:

    def chat(self, message: str) -> str:
        return f"You said: {message}"