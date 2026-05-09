# ============================================================
# UltraAgent — memory/memory_router.py
# بيقرر إيه اللي يتحفظ فين
# ============================================================

import structlog
from .short_term import short_term
from .long_term import long_term

log = structlog.get_logger()

# أدنى importance عشان يتحفظ في long-term
IMPORTANCE_THRESHOLD = 0.6


class MemoryRouter:
    """
    بيوجّه الذكريات:
    - كل حاجة → short_term (Redis) للجلسة
    - الحاجات المهمة (importance >= threshold) → long_term (Supabase)
    """

    def save(
        self,
        chat_id: str,
        role: str,
        content: str,
        importance: float = 0.5,
        source: str = "user",
    ) -> None:
        """بيحفظ في short-term دايماً، وفي long-term لو مهم."""
        short_term.add_message(chat_id, role, content)

        if importance >= IMPORTANCE_THRESHOLD:
            long_term.save(content, source=source, importance=importance)
            log.info("memory_router_long_term", importance=importance)

    def get_context(self, chat_id: str, query: str) -> dict:
        """
        بيجيب:
        - messages الجلسة الحالية من Redis
        - ذكريات ذات صلة من Supabase
        """
        session_messages = short_term.get_messages(chat_id)
        relevant_memories = long_term.search(query, top_k=3)

        memory_texts = [m.get("content", "") for m in relevant_memories]

        return {
            "session_messages": session_messages,
            "long_term_context": memory_texts,
        }


# Singleton
memory_router = MemoryRouter()
