"""智能体后端（独立服务，端口 8004）。

- POST /api/agent/chat：NDJSON 流式对话（事件：text/tool/image/done/error）。
- GET  /api/health：联通检查。
- /outputs：静态托管运行期生成的 PNG。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.llm import run_chat
from config import DEEPSEEK_MODEL, OUTPUTS_DIR, has_llm

app = FastAPI(title="Weather Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5177", "http://127.0.0.1:5177",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")


def ok(data: Any = None, message: str = "success") -> dict[str, Any]:
    return {"code": 0, "data": data, "message": message}


class ChatMessage(BaseModel):
    role: str
    content: str = ""


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []
    context: dict[str, Any] = {}


@app.get("/")
def root() -> dict[str, Any]:
    return ok({"service": "weather-agent-backend", "docs": "/docs"})


@app.get("/api/health")
def health() -> dict[str, Any]:
    return ok({
        "status": "online",
        "service": "backend_agent",
        "llm_ready": has_llm(),
        "model": DEEPSEEK_MODEL,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }, "backend_agent connected")


@app.post("/api/agent/chat")
def agent_chat(req: ChatRequest) -> StreamingResponse:
    history = [m.model_dump() for m in req.messages]

    def event_stream() -> Iterator[bytes]:
        for evt in run_chat(history):
            yield (json.dumps(evt, ensure_ascii=False) + "\n").encode("utf-8")

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8004, reload=True)
