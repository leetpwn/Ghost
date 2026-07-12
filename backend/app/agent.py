from langchain_ollama import ChatOllama
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from app.prompts import SYSTEM_PROMPT
from app.tools import TOOLS

TOOL_BY_NAME = {
    tool.name: tool
    for tool in TOOLS
}

class GhostAgent:
    def __init__(self):
        self.llm = ChatOllama(
            model="qwen3:8b",
            temperature=0,
        )

        self.llm_with_tools = self.llm.bind_tools(
            TOOLS
        )

    def chat(self, message: str) -> str:

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=message),
        ]

        # First LLM call
        ai_message = self.llm_with_tools.invoke(messages)

        messages.append(ai_message)

        # Did the model request any tools?
        if ai_message.tool_calls:

            for tool_call in ai_message.tool_calls:

                tool = TOOL_BY_NAME[tool_call["name"]]

                result = tool.invoke(tool_call["args"])

                messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"],
                    )
                )

            final_response = self.llm_with_tools.invoke(messages)

            return final_response.content
        
        # No tool needed
        return ai_message.content