# ============================================================
# UltraAgent — advanced/guardrails.py
# حماية من التكاليف المفرطة والأفعال الخطيرة
# ============================================================

import os
import structlog
from memory.short_term import short_term

log = structlog.get_logger()

RISKY_ACTIONS = ["delete", "send_email", "post", "payment", "transfer", "remove"]
MAX_CHAIN_DEPTH = 5


class Guardrails:
    def __init__(self):
        self.max_daily = int(os.getenv("MAX_DAILY_REQUESTS", "500"))

    def check_request(self) -> bool:
        """هل مازلنا تحت الحد اليومي؟"""
        count = short_term.increment_daily_counter()
        if count > self.max_daily:
            log.warning("guardrail_daily_limit", count=count, max=self.max_daily)
            return False
        return True

    def is_risky(self, action: str) -> bool:
        """هل الفعل ده خطير ومحتاج موافقة؟"""
        action_lower = action.lower()
        return any(risky in action_lower for risky in RISKY_ACTIONS)

    def check_chain_depth(self, depth: int) -> bool:
        """هل وصلنا الحد الأقصى للـ chain؟"""
        if depth >= MAX_CHAIN_DEPTH:
            log.warning("guardrail_chain_depth", depth=depth)
            return False
        return True


guardrails = Guardrails()
