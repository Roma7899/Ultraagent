# ============================================================
# UltraAgent — agents/file_agent.py
# بيتعامل مع Supabase Storage
# ============================================================

import os
import structlog
from supabase import create_client
from .base_agent import BaseAgent, AgentResult

log = structlog.get_logger()
BUCKET = "ultraagent-files"


class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__("file_agent")
        self._db = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_KEY", ""),
        )

    def _execute(self, task: str, context: dict) -> AgentResult:
        action = context.get("action", "read")
        filename = context.get("filename", "")
        content = context.get("content", b"")

        try:
            if action == "write":
                self._db.storage.from_(BUCKET).upload(
                    filename,
                    content.encode() if isinstance(content, str) else content,
                    {"content-type": "text/plain"},
                )
                return AgentResult(success=True, output=f"تم رفع {filename}")

            elif action == "read":
                data = self._db.storage.from_(BUCKET).download(filename)
                return AgentResult(success=True, output=data.decode("utf-8", errors="replace"))

            elif action == "list":
                files = self._db.storage.from_(BUCKET).list()
                return AgentResult(success=True, output=[f["name"] for f in files])

            else:
                return AgentResult(success=False, output=None, error=f"action غير معروف: {action}")

        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))


file_agent = FileAgent()
