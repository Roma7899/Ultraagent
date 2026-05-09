# ============================================================
# UltraAgent — agents/research_agent.py
# بيبحث على الويب باستخدام Tavily ثم يلخص بـ NIM
# ============================================================

import os
import structlog
from tavily import TavilyClient

from .base_agent import BaseAgent, AgentResult
from llm.fallback_chain import fallback_chain

log = structlog.get_logger()


class ResearchAgent(BaseAgent):
    """
    Agent للبحث على الويب.
    1. بيبحث بـ Tavily (أسرع وأدق من Google scraping)
    2. بيمرر النتائج لـ NIM عشان يلخص ويستخلص
    """

    def __init__(self):
        super().__init__("research_agent")
        api_key = os.getenv("TAVILY_API_KEY", "")
        self._tavily = TavilyClient(api_key=api_key)

    def _execute(self, task: str, context: dict) -> AgentResult:
        # ── الخطوة 1: البحث بـ Tavily ──
        try:
            search_result = self._tavily.search(
                query=task,
                max_results=5,
                search_depth="advanced",
                include_answer=True,
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=f"Tavily error: {e}")

        results = search_result.get("results", [])
        tavily_answer = search_result.get("answer", "")

        if not results:
            return AgentResult(
                success=False,
                output=None,
                error="مفيش نتائج للبحث",
            )

        # ── الخطوة 2: تلخيص بـ NIM ──
        snippets = "\n\n".join([
            f"المصدر: {r.get('url', '')}\n{r.get('content', '')[:500]}"
            for r in results
        ])

        prompt = f"""بحثت عن: "{task}"

النتائج من الويب:
{snippets}

{"الإجابة المباشرة: " + tavily_answer if tavily_answer else ""}

اكتب ملخصاً مفيداً بالعربية يجيب على السؤال بشكل مباشر. اذكر المصادر في النهاية."""

        try:
            summary, model_used = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )
        except Exception as e:
            # لو فشل التلخيص، نرجع الـ snippets الخام
            summary = snippets
            model_used = "none"

        # احفظ النتيجة في الذاكرة
        self.save_memory(f"بحث: {task}\nنتيجة: {summary[:300]}", importance=0.6)

        return AgentResult(
            success=True,
            output={
                "summary": summary,
                "sources": [r.get("url", "") for r in results],
                "raw_results": results,
            },
            model_used=model_used,
        )


# Singleton
research_agent = ResearchAgent()
