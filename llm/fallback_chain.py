# ============================================================
# UltraAgent — llm/fallback_chain.py
# بيجرب موديلات بالترتيب لحد ما واحد ينجح
# ✅ محدّث بأحدث موديلات NVIDIA NIM (مايو 2026)
# ============================================================

import time
import structlog
from .nim_client import nim_client, NIMError

log = structlog.get_logger()


class FallbackExhausted(Exception):
    """رُفع لما كل الموديلات فشلت."""
    pass


# ============================================================
# ترتيب الأولوية: الأقوى أول، الأخف آخر
# كل الموديلات دي متاحة مجاناً على NVIDIA NIM (مايو 2026)
# ============================================================
FALLBACK_MODELS = [
    "deepseek-ai/deepseek-v4-flash",         # الأول: أقوى reasoning + 1M context - مخصص للـ agents
    "mistralai/kimi-k2-instruct",            # الثاني: context طويل + tool use ممتاز
    "zhipuai/glm-5.1",                       # الثالث: multilingual + agentic workflows
    "minimax/minimax-m2.7",                  # الرابع: 230B reasoning قوي
    "nvidia/nemotron-nano-8b-instruct",      # الخامس: خفيف جداً للـ fallback النهائي
]

# موديلات بديلة لو الأساسية فشلت كلها
EMERGENCY_FALLBACK_MODELS = [
    "meta/llama-3.3-70b-instruct",          # Llama 3.3 70B - مستقر جداً
    "mistralai/mistral-large-2-instruct",   # Mistral Large 2
    "qwen/qwen3-235b-a22b",                 # Qwen3 235B
]


class FallbackChain:
    """
    بيلف على الموديلات بالترتيب.
    لو NIMError → جرب التالي.
    لو كلهم فشلوا → جرب Emergency models.
    لو كلهم فشلوا → FallbackExhausted.
    """

    def __init__(self, models: list[str] = None, emergency_models: list[str] = None):
        self.models = models or FALLBACK_MODELS
        self.emergency_models = emergency_models or EMERGENCY_FALLBACK_MODELS

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
        all_models = self.models + self.emergency_models

        for model in all_models:
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
                error_str = str(e)
                log.warning("fallback_model_failed", model=model, reason=error_str)
                errors.append(f"{model}: {error_str}")

                # لو الموديل End of Life أو Gone (410) → تخطى فوراً
                if "410" in error_str or "end of life" in error_str.lower() or "gone" in error_str.lower():
                    log.warning("model_eol_skipping", model=model)
                    continue

                # لو rate limit (429) → انتظر ثانيتين وجرب التالي
                if "429" in error_str or "rate" in error_str.lower():
                    log.warning("rate_limit_waiting", model=model)
                    time.sleep(2)
                    continue

                continue

        log.error("fallback_exhausted", tried=all_models, errors=errors)
        raise FallbackExhausted(
            f"كل الموديلات فشلت:\n" + "\n".join(errors)
        )


# Singleton
fallback_chain = FallbackChain()
