# ============================================================
# UltraAgent — memory/long_term.py
# ذاكرة طويلة المدى باستخدام Supabase + pgvector
# ============================================================

import os
import uuid
import json
import structlog
from datetime import datetime, timezone
from supabase import create_client, Client
from llm.fallback_chain import fallback_chain

log = structlog.get_logger()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LongTermMemory:
    """
    بتخزن وتسترجع الذكريات المهمة باستخدام:
    - Supabase: لتخزين النصوص والـ metadata
    - pgvector: للبحث بالتشابه الدلالي
    - NIM embedding: لتحويل النص لـ vector
    """

    EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"
    TABLE = "memories"

    def __init__(self):
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        self._db: Client = create_client(url, key)

    def _embed(self, text: str) -> list[float]:
        """بيحول النص لـ vector باستخدام NIM embedding."""
        try:
            # نستخدم الـ NIM client مباشرة للـ embeddings
            import os
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
        """
        بيحفظ ذكرى جديدة.
        Returns: id الذكرى
        """
        try:
            embedding = self._embed(content)
            entry_id = str(uuid.uuid4())
            now = _now()

            self._db.table(self.TABLE).insert({
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

            log.info("memory_saved", id=entry_id, source=source)
            return entry_id

        except Exception as e:
            log.error("memory_save_error", error=str(e))
            return ""

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        بيبحث في الذكريات باستخدام cosine similarity.
        Returns: list من الذكريات الأكثر صلة
        """
        try:
            query_embedding = self._embed(query)
            if not query_embedding:
                return []

            # RPC function في Supabase بتعمل vector search
            result = self._db.rpc(
                "search_memories",
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                }
            ).execute()

            memories = result.data or []

            # نحدث last_accessed لكل ذكرى اترجعت
            for mem in memories:
                self._update_access(mem["id"])

            log.info("memory_search", query_preview=query[:50], found=len(memories))
            return memories

        except Exception as e:
            log.error("memory_search_error", error=str(e))
            return []

    def _update_access(self, memory_id: str) -> None:
        """بيحدث last_accessed و access_count."""
        try:
            self._db.rpc("increment_memory_access", {"memory_id": memory_id}).execute()
        except Exception:
            pass

    def consolidate(self) -> int:
        """
        بيدمج الذكريات المتشابهة — بيتنادى من Dreaming Mode.
        Returns: عدد الذكريات اللي اتدمجت
        """
        try:
            # اجلب الذكريات غير المدمجة من آخر 7 أيام
            result = self._db.table(self.TABLE)\
                .select("*")\
                .eq("consolidated", False)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()

            memories = result.data or []
            if len(memories) < 2:
                return 0

            # اطلب من NIM يلخصهم
            content_list = "\n---\n".join([m["content"] for m in memories[:20]])
            prompt = f"""لديك هذه الذكريات:
{content_list}

اكتب ملخصاً موحداً يحتفظ بأهم المعلومات. كن مختصراً."""

            summary, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
            )

            # احفظ الملخص كذكرى مهمة
            self.save(summary, source="dreaming", importance=0.9)

            # علّم الذكريات الأصلية كـ consolidated
            ids = [m["id"] for m in memories[:20]]
            self._db.table(self.TABLE)\
                .update({"consolidated": True})\
                .in_("id", ids)\
                .execute()

            log.info("memory_consolidated", count=len(ids))
            return len(ids)

        except Exception as e:
            log.error("memory_consolidate_error", error=str(e))
            return 0


# Singleton
long_term = LongTermMemory()
