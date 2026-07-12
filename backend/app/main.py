# Entrypoint to the backend
# The goal of this file is to start the backend FastAPI server, expose API endpoints, call the agent and return the resposne. 


from fastapi import FastAPI
from app.agent import GhostAgent
from app.models import ChatRequest, ChatResponse

app = FastAPI(title="Ghost")

agent = GhostAgent()


@app.get("/")
def root():
    return {"message": "Welcome to Ghost Terminal👻"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    response = agent.chat(request.message)
    return ChatResponse(response=response)