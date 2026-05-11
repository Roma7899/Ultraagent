# UltraAgent — agents/base_agent.py

import time
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

log = structlog.get_logger()


@dataclass
class AgentResult:
    success: bool
    output: Any
    error: str = ""
    latency_ms: int = 0
    model_used: str = ""


class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._log = log.bind(agent=agent_id)

    @abstractmethod
    def _execute(self, task: str, context: dict) -> AgentResult:
        ...

    def run(self, task: str, context: dict | None = None) -> AgentResult:
        context = context or {}
        start = time.time()
        self._log.info("agent_start", task_preview=task[:80])
        try:
            result = self._execute(task, context)
            result.latency_ms = int((time.time() - start) * 1000)
            self._log.info("agent_done", success=result.success, latency_ms=result.latency_ms)
            return result
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            self._log.error("agent_exception", error=str(e))
            return AgentResult(success=False, output=None, error=str(e), latency_ms=latency_ms)

    def get_memory(self, query: str, top_k: int = 3) -> list[str]:
        try:
            from memory.long_term import long_term
            results = long_term.search(query, top_k=top_k)
            return [r.get("content", "") for r in results]
        except Exception:
            return []

    def save_memory(self, content: str, importance: float = 0.5) -> None:
        try:
            from memory.long_term import long_term
            long_term.save(content, source=self.agent_id, importance=importance)
        except Exception:
            pass
