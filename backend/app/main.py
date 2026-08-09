# Entrypoint to the backend

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent import GhostAgent
from app.models import ChatRequest, ChatResponse
from app.api.network import router as network_router
from app.network.service import network_monitor


agent = GhostAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(
        network_monitor.start()
    )

    try:
        yield
    finally:
        network_monitor.stop()
        await monitor_task


app = FastAPI(
    title="Ghost",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "Welcome to Ghost Terminal👻"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    response = agent.chat(request.message)

    return ChatResponse(
        response=response
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ghost",
    }


# New network functionality
app.include_router(network_router)