# ============================================================
# UltraAgent — memory/long_term.py
# ذاكرة طويلة المدى باستخدام Supabase + pgvector
# ============================================================

import os
import uuid
import structlog
from datetime import datetime, timezone

log = structlog.get_logger()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LongTermMemory:
    EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    TABLE = "memories"

    def __init__(self):
        # ⚠️ لا نعمل create_client هنا — بنعمله lazy عند أول استخدام
        self._db = None

    def _get_db(self):
        """Lazy initialization — بيتعمل أول ما نحتاجه فعلاً."""
        if self._db is None:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_KEY", "")
            if not url or not key:
                raise EnvironmentError("SUPABASE_URL أو SUPABASE_KEY مش موجودين")
            self._db = create_client(url, key)
        return self._db

    def _embed(self, text: str) -> list[float]:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=os.getenv("NVIDIA_API_KEY"),
                base_url="https://integrate.api.nvidia.com/v1",
            )
            response = client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text,
                encoding_format="float",
            )
            return response.data[0].embedding
        except Exception as e:
            log.warning("embedding_error", error=str(e))
            return []

    def save(self, content: str, source: str = "agent", importance: float = 0.5) -> str:
        try:
            db = self._get_db()
            embedding = self._embed(content)
            entry_id = str(uuid.uuid4())
            now = _now()
            db.table(self.TABLE).insert({
                "id": entry_id,
                "content": content,
                "embedding": embedding,
                "source": source,
                "importance": importance,
                "consolidated": False,
                "created_at": now,
                "last_accessed": now,
                "access_count": 0,
            }).execute()
            log.info("memory_saved", id=entry_id)
            return entry_id
        except Exception as e:
            log.error("memory_save_error", error=str(e))
            return ""

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        try:
            db = self._get_db()
            query_embedding = self._embed(query)
            if not query_embedding:
                return []
            result = db.rpc("search_memories", {
                "query_embedding": query_embedding,
                "match_count": top_k,
            }).execute()
            return result.data or []
        except Exception as e:
            log.error("memory_search_error", error=str(e))
            return []

    def _update_access(self, memory_id: str) -> None:
        try:
            self._get_db().rpc("increment_memory_access", {"memory_id": memory_id}).execute()
        except Exception:
            pass

    def consolidate(self) -> int:
        try:
            db = self._get_db()
            from llm.fallback_chain import fallback_chain
            result = db.table(self.TABLE)\
                .select("*")\
                .eq("consolidated", False)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            memories = result.data or []
            if len(memories) < 2:
                return 0
            content_list = "\n---\n".join([m["content"] for m in memories[:20]])
            prompt = f"لديك هذه الذكريات:\n{content_list}\n\nاكتب ملخصاً موحداً مختصراً."
            summary, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )
            self.save(summary, source="dreaming", importance=0.9)
            ids = [m["id"] for m in memories[:20]]
            db.table(self.TABLE).update({"consolidated": True}).in_("id", ids).execute()
            return len(ids)
        except Exception as e:
            log.error("memory_consolidate_error", error=str(e))
            return 0


# Singleton
long_term = LongTermMemory()
