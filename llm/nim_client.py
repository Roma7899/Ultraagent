# ============================================================
# UltraAgent — llm/nim_client.py
# العميل الوحيد لكل calls على NVIDIA NIM
# ============================================================

import os
import time
import structlog
from openai import OpenAI, APIError, APITimeoutError

log = structlog.get_logger()


class NIMError(Exception):
    """رُفع لما يفشل الـ NIM call — fallback_chain هيمسكه."""
    pass


class NIMClient:
    """
    Thin wrapper حول OpenAI SDK موجّه لـ NVIDIA NIM endpoint.
    كل الـ agents بتتكلم معاه بدل ما تتكلم مع OpenAI مباشرة.
    """

    BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(self):
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise EnvironmentError("NVIDIA_API_KEY مش موجود في الـ environment variables")

        self._client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
            timeout=60.0,
        )

    def call(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """
        بيعمل call على NIM model معين.

        Args:
            model:      اسم الموديل زي "deepseek-ai/deepseek-r1"
            messages:   list of {"role": "user/assistant/system", "content": "..."}
            max_tokens: أقصى عدد tokens في الرد
            temperature: درجة الإبداع (0 = محدد، 1 = مبدع)

        Returns:
            نص الرد كـ string

        Raises:
            NIMError: لو فشل الـ call لأي سبب
        """
        start = time.time()
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content or ""
            latency_ms = int((time.time() - start) * 1000)
            log.info("nim_call_success", model=model, latency_ms=latency_ms, tokens=len(text.split()))
            return text

        except APITimeoutError as e:
            log.warning("nim_timeout", model=model)
            raise NIMError(f"Timeout على موديل {model}") from e

        except APIError as e:
            log.warning("nim_api_error", model=model, status=e.status_code, message=str(e))
            raise NIMError(f"API error على موديل {model}: {e}") from e

        except Exception as e:
            log.error("nim_unexpected_error", model=model, error=str(e))
            raise NIMError(f"خطأ غير متوقع مع موديل {model}: {e}") from e


# Singleton — كل الـ codebase بتستخدم نفس الـ instance
nim_client = NIMClient()
