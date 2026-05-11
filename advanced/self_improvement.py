# ============================================================
# UltraAgent — advanced/self_improvement.py
# بيحسن الـ prompts أسبوعياً بناءً على الأداء
# ============================================================

import os
import structlog
from supabase import create_client
from llm.fallback_chain import fallback_chain

log = structlog.get_logger()


class SelfImprovement:
    def __init__(self):
        self._db = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", ""),
        )

    def run_weekly(self) -> dict:
        """بيتنادى كل أسبوع من الـ cron."""
        try:
            # اجلب المهام الفاشلة من الأسبوع الماضي
            result = self._db.table("task_history")\
                .select("task, result, agent_used")\
                .eq("success", False)\
                .limit(20)\
                .execute()

            failures = result.data or []
            if not failures:
                log.info("self_improvement_no_failures")
                return {"improved": 0}

            failures_text = "\n".join([
                f"- المهمة: {f['task'][:100]}\n  السبب: {str(f['result'])[:100]}"
                for f in failures[:10]
            ])

            prompt = f"""هذه المهام فشل تنفيذها:
{failures_text}

اقترح تحسينات للـ system prompt الخاص بالـ orchestrator لتفادي هذه الأخطاء مستقبلاً.
اكتب system prompt محسّن فقط."""

            improved_prompt, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
            )

            # احفظ الـ prompt الجديد
            self._db.table("prompt_versions").insert({
                "agent_type": "orchestrator",
                "prompt_text": improved_prompt,
                "version": 1,
                "active": False,
                "traffic_pct": 20,
            }).execute()

            log.info("self_improvement_done", failures_analyzed=len(failures))
            return {"improved": len(failures), "new_prompt_saved": True}

        except Exception as e:
            log.error("self_improvement_error", error=str(e))
            return {"error": str(e)}


self_improvement = SelfImprovement()
