# ============================================================
# UltraAgent — interfaces/rest_api.py
# FastAPI endpoints
# ============================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.orchestrator import run_task

app = FastAPI(title="UltraAgent API", version="1.0.0")


class TaskRequest(BaseModel):
    task: str
    chat_id: str = "api_user"


class TaskResponse(BaseModel):
    response: str
    status: str = "success"


@app.get("/")
def health():
    return {"status": "ok", "agent": "UltraAgent v1.0"}


@app.post("/task", response_model=TaskResponse)
def execute_task(req: TaskRequest):
    try:
        response = run_task(req.task, req.chat_id)
        return TaskResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
