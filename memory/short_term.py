# ============================================================
# UltraAgent — memory/short_term.py
# ذاكرة الجلسة على Redis (Upstash)
# ============================================================

import os
import json
import structlog
import redis

log = structlog.get_logger()

# مدة الجلسة: 2 ساعة
SESSION_TTL_SECONDS = 7200


class ShortTermMemory:
    """
    بتخزن messages المحادثة الحالية في Redis.
    كل session عندها key منفصل بـ chat_id.
    """

    def __init__(self):
        url = os.getenv("REDIS_URL", "")
        password = os.getenv("REDIS_PASSWORD", "")
        self._client = redis.from_url(
            url,
            password=password,
            decode_responses=True,
        )

    def _key(self, chat_id: str) -> str:
        return f"session:{chat_id}"

    def get_messages(self, chat_id: str) -> list[dict]:
        """بيرجع تاريخ المحادثة."""
        try:
            raw = self._client.get(self._key(chat_id))
            return json.loads(raw) if raw else []
        except Exception as e:
            log.warning("short_term_get_error", chat_id=chat_id, error=str(e))
            return []

    def add_message(self, chat_id: str, role: str, content: str) -> None:
        """بيضيف message ويجدد الـ TTL."""
        try:
            messages = self.get_messages(chat_id)
            messages.append({"role": role, "content": content})
            # خلي الـ history محدود بـ 20 message
            messages = messages[-20:]
            self._client.setex(
                self._key(chat_id),
                SESSION_TTL_SECONDS,
                json.dumps(messages, ensure_ascii=False),
            )
        except Exception as e:
            log.warning("short_term_add_error", chat_id=chat_id, error=str(e))

    def clear(self, chat_id: str) -> None:
        """بيمسح جلسة بالكامل."""
        try:
            self._client.delete(self._key(chat_id))
        except Exception as e:
            log.warning("short_term_clear_error", chat_id=chat_id, error=str(e))

    def increment_daily_counter(self) -> int:
        """بيزود عداد الـ requests اليومي ويرجع القيمة الحالية."""
        try:
            key = "daily:requests"
            count = self._client.incr(key)
            # بيعمل expire على نهاية اليوم (86400 ثانية)
            self._client.expire(key, 86400)
            return int(count)
        except Exception as e:
            log.warning("daily_counter_error", error=str(e))
            return 0

    def get_daily_count(self) -> int:
        """بيرجع عدد الـ requests النهارده."""
        try:
            val = self._client.get("daily:requests")
            return int(val) if val else 0
        except Exception:
            return 0


# Singleton
short_term = ShortTermMemory()
