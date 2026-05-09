# ============================================================
# UltraAgent — agents/automation_agent.py
# بيعمل HTTP calls وwebhook triggers
# ============================================================

import httpx
import structlog
from .base_agent import BaseAgent, AgentResult
from llm.fallback_chain import fallback_chain

log = structlog.get_logger()


class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__("automation_agent")

    def _execute(self, task: str, context: dict) -> AgentResult:
        # NIM بيحدد الـ HTTP call المطلوب
        prompt = f"""المهمة: {task}

حدد الـ HTTP request المطلوب بصيغة JSON فقط:
{{
  "method": "GET|POST|PUT|DELETE",
  "url": "...",
  "headers": {{}},
  "body": {{}}
}}"""
        try:
            plan_text, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1,
            )
            import json, re
            match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if not match:
                return AgentResult(success=False, output=None, error="مش قادر أفهم الـ HTTP call المطلوب")

            call_spec = json.loads(match.group())
            method = call_spec.get("method", "GET").upper()
            url = call_spec.get("url", "")
            headers = call_spec.get("headers", {})
            body = call_spec.get("body", {})

            with httpx.Client(timeout=30) as client:
                resp = client.request(method, url, headers=headers, json=body if body else None)

            return AgentResult(
                success=resp.status_code < 400,
                output={"status": resp.status_code, "body": resp.text[:1000]},
            )
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))


automation_agent = AutomationAgent()
