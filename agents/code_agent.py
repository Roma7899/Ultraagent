# ============================================================
# UltraAgent — agents/code_agent.py
# بيكتب وينفذ كود Python في E2B sandbox آمن
# ============================================================

import os
import structlog
from e2b_code_interpreter import Sandbox

from .base_agent import BaseAgent, AgentResult
from llm.fallback_chain import fallback_chain

log = structlog.get_logger()

MAX_RETRIES = 3


class CodeAgent(BaseAgent):
    """
    Agent للكود:
    1. NIM بيكتب الكود
    2. E2B بينفذه في sandbox معزول
    3. لو في error → NIM بيصلح → retry (max 3)
    """

    def __init__(self):
        super().__init__("code_agent")

    def _execute(self, task: str, context: dict) -> AgentResult:
        # ── الخطوة 1: توليد الكود ──
        code = self._generate_code(task, error_context="")
        if not code:
            return AgentResult(success=False, output=None, error="فشل توليد الكود")

        # ── الخطوة 2: تنفيذ مع retry ──
        for attempt in range(1, MAX_RETRIES + 1):
            exec_result = self._run_in_sandbox(code)

            if exec_result["success"]:
                self.save_memory(
                    f"كود لـ: {task}\n```python\n{code}\n```",
                    importance=0.7,
                )
                return AgentResult(
                    success=True,
                    output={
                        "code": code,
                        "stdout": exec_result["stdout"],
                        "result": exec_result["result"],
                    },
                )
            else:
                log.warning("code_agent_retry", attempt=attempt, error=exec_result["stderr"])
                if attempt < MAX_RETRIES:
                    code = self._generate_code(task, error_context=exec_result["stderr"])
                    if not code:
                        break

        return AgentResult(
            success=False,
            output={"code": code},
            error=f"فشل التنفيذ بعد {MAX_RETRIES} محاولات",
        )

    def _generate_code(self, task: str, error_context: str) -> str:
        """بيطلب من NIM يكتب كود Python."""
        error_part = f"\n\nالكود الأول أعطى الخطأ التالي، صلحه:\n{error_context}" if error_context else ""

        prompt = f"""اكتب كود Python ينفذ المطلوب التالي:
{task}{error_part}

متطلبات:
- اكتب الكود فقط بدون شرح
- لا تستخدم مكتبات خارجية غير موجودة في Python standard library (إلا numpy وpandas وrequests)
- استخدم print() لعرض النتيجة
- الكود يجب أن يكون قابلاً للتنفيذ مباشرة"""

        try:
            code_text, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3,
            )
            # استخرج الكود من الـ markdown لو موجود
            if "```python" in code_text:
                code_text = code_text.split("```python")[1].split("```")[0]
            elif "```" in code_text:
                code_text = code_text.split("```")[1].split("```")[0]
            return code_text.strip()
        except Exception as e:
            log.error("code_generation_failed", error=str(e))
            return ""

    def _run_in_sandbox(self, code: str) -> dict:
        """بينفذ الكود في E2B sandbox."""
        try:
            with Sandbox(api_key=os.getenv("E2B_API_KEY", "")) as sandbox:
                execution = sandbox.run_code(code)
                stdout = "\n".join([str(o) for o in execution.logs.stdout])
                stderr = "\n".join([str(o) for o in execution.logs.stderr])
                result = execution.results[0].text if execution.results else ""

                return {
                    "success": not execution.error,
                    "stdout": stdout,
                    "stderr": stderr or (str(execution.error) if execution.error else ""),
                    "result": result,
                }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "result": ""}


# Singleton
code_agent = CodeAgent()
