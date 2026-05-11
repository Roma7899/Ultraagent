# ============================================================
# UltraAgent — core/state.py
# الـ dataclass المشترك بين كل الـ nodes في LangGraph
# ============================================================

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    """
    الحالة الكاملة للـ agent في أي لحظة.
    LangGraph بيمرر الـ object ده بين الـ nodes.
    """

    # المهمة الأصلية من المستخدم
    task: str = ""

    # تاريخ المحادثة كاملاً
    messages: list[dict] = field(default_factory=list)

    # الخطوات اللي الـ orchestrator قرر يعملها
    plan: list[str] = field(default_factory=list)

    # رقم الخطوة الحالية
    current_step: int = 0

    # نتائج كل sub-agent
    results: dict[str, Any] = field(default_factory=dict)

    # الـ agents اللي شغالة دلوقتي
    active_agents: list[str] = field(default_factory=list)

    # ذكريات من الـ long-term memory
    memory_context: list[str] = field(default_factory=list)

    # هل بننتظر موافقة المستخدم؟
    awaiting_human: bool = False

    # عداد الأخطاء (للـ fallback logic)
    error_count: int = 0

    # الـ agents اللي اتعملت at runtime
    spawned_agents: list[dict] = field(default_factory=list)

    # metadata: تكلفة، وقت، اسم الموديل المستخدم
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        """بيضيف message للتاريخ."""
        self.messages.append({"role": role, "content": content})

    def set_result(self, agent_name: str, result: Any) -> None:
        """بيحفظ نتيجة agent معين."""
        self.results[agent_name] = result

    def next_step(self) -> str | None:
        """بيرجع الخطوة الجاية أو None لو خلصنا."""
        if self.current_step < len(self.plan):
            step = self.plan[self.current_step]
            self.current_step += 1
            return step
        return None

    def is_done(self) -> bool:
        """هل خلصنا كل الخطوات؟"""
        return self.current_step >= len(self.plan)


@dataclass
class AgentReputation:
    """سجل أداء كل agent."""
    agent_id: str
    total_tasks: int = 0
    successful_tasks: int = 0
    avg_latency_ms: float = 0.0
    last_failure_reason: str = ""
    score: float = 0.8  # يبدأ بـ 0.8 (ثقة افتراضية)

    def update(self, success: bool, latency_ms: float) -> None:
        """بيحدث الـ score بعد كل task."""
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        # moving average للـ latency
        self.avg_latency_ms = (
            (self.avg_latency_ms * (self.total_tasks - 1) + latency_ms)
            / self.total_tasks
        )
        self._recalculate_score()

    def _recalculate_score(self) -> None:
        if self.total_tasks == 0:
            return
        success_rate = self.successful_tasks / self.total_tasks
        # normalize latency: أسرع من 2 ثانية = 1.0، أبطأ من 10 ثواني = 0.0
        max_latency = 10_000
        speed_score = max(0.0, 1.0 - (self.avg_latency_ms / max_latency))
        self.score = round(success_rate * 0.7 + speed_score * 0.3, 3)


@dataclass
class MemoryEntry:
    """مدخل واحد في الـ long-term memory."""
    id: str
    content: str
    embedding: list[float] = field(default_factory=list)
    source: str = "unknown"
    importance: float = 0.5
    created_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
