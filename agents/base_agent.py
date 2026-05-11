# ============================================================
# UltraAgent — agents/base_agent.py
# الـ parent class اللي كل الـ agents بترثه
# ============================================================

import time
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from core.state import AgentReputation
from memory.long_term import long_term

log = structlog.get_logger()


@dataclass
class AgentResult:
    """نتيجة أي agent."""
    success: bool
    output: Any
    error: str = ""
    latency_ms: int = 0
    model_used: str = ""


class BaseAgent(ABC):
    """
    كل الـ agents بترث منه.
    بيوفر: logging، reputation tracking، memory helpers.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.reputation = AgentReputation(agent_id=agent_id)
        self._log = log.bind(agent=agent_id)

    @abstractmethod
    def _execute(self, task: str, context: dict) -> AgentResult:
        """كل agent بيعمل override لهذه الدالة."""
        ...

    def run(self, task: str, context: dict | None = None) -> AgentResult:
        """
        بينادي _execute ويعمل logging وreputation update.
        """
        context = context or {}
        start = time.time()
        self._log.info("agent_start", task_preview=task[:80])

        try:
            result = self._execute(task, context)
            result.latency_ms = int((time.time() - start) * 1000)
            self.reputation.update(success=result.success, latency_ms=result.latency_ms)
            self._log.info(
                "agent_done",
                success=result.success,
                latency_ms=result.latency_ms,
            )
            return result

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            self.reputation.update(success=False, latency_ms=latency_ms)
            self.reputation.last_failure_reason = str(e)
            self._log.error("agent_exception", error=str(e))
            return AgentResult(success=False, output=None, error=str(e), latency_ms=latency_ms)

    def get_memory(self, query: str, top_k: int = 3) -> list[str]:
        """بيبحث في الـ long-term memory."""
        results = long_term.search(query, top_k=top_k)
        return [r.get("content", "") for r in results]

    def save_memory(self, content: str, importance: float = 0.5) -> None:
        """بيحفظ في الـ long-term memory."""
        long_term.save(content, source=self.agent_id, importance=importance)
