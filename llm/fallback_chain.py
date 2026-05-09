# ============================================================
# UltraAgent — llm/fallback_chain.py
# بيجرب موديلات بالترتيب لحد ما واحد ينجح
# ============================================================

import time
import structlog
from .nim_client import nim_client, NIMError

log = structlog.get_logger()


class FallbackExhausted(Exception):
    """رُفع لما كل الموديلات فشلت."""
    pass


# ترتيب الأولوية: الأقوى أول، الأخف آخر
FALLBACK_MODELS = [
    "deepseek-ai/deepseek-r1",           # الأول: أقوى reasoning
    "mistralai/kimi-k2-instruct",        # الثاني: context طويل
    "tiiuae/falcon3-10b-instruct",       # الثالث: سريع
    "nvidia/nemotron-nano-8b-instruct",  # الرابع: خفيف جداً
]


class FallbackChain:
    """
    بيلف على الموديلات بالترتيب.
    لو NIMError → جرب التالي.
    لو كلهم فشلوا → FallbackExhausted.
    """

    def __init__(self, models: list[str] = None):
        self.models = models or FALLBACK_MODELS

    def complete(
        self,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> tuple[str, str]:
        """
        بيحاول يكمل الـ messages باستخدام أول موديل ينجح.

        Returns:
            (text, model_used) — نص الرد + اسم الموديل اللي اشتغل

        Raises:
            FallbackExhausted: لو كل الموديلات فشلت
        """
        errors = []

        for model in self.models:
            try:
                log.info("fallback_trying", model=model)
                start = time.time()
                text = nim_client.call(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                latency_ms = int((time.time() - start) * 1000)
                log.info("fallback_success", model=model, latency_ms=latency_ms)
                return text, model

            except NIMError as e:
                log.warning("fallback_model_failed", model=model, reason=str(e))
                errors.append(f"{model}: {e}")
                continue

        log.error("fallback_exhausted", tried=self.models, errors=errors)
        raise FallbackExhausted(
            f"كل الموديلات فشلت:\n" + "\n".join(errors)
        )


# Singleton
fallback_chain = FallbackChain()
