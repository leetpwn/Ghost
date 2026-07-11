# Handles user requests and decides how Ghost should respond.

from langchain_ollama import ChatOllama


class GhostAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:8b",
            temperature=0,
        )

    def chat(self, message: str) -> str:
        response = self.llm.invoke(message)
        return response.content