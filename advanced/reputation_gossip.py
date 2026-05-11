# ============================================================
# UltraAgent — advanced/reputation.py
# ============================================================
import os, structlog
from supabase import create_client
log = structlog.get_logger()

class ReputationSystem:
    SUSPEND_THRESHOLD = 0.3
    PREFER_THRESHOLD = 0.7

    def __init__(self):
        self._db = create_client(os.getenv("SUPABASE_URL",""), os.getenv("SUPABASE_KEY",""))

    def update(self, agent_id: str, success: bool, latency_ms: float) -> None:
        try:
            result = self._db.table("agent_reputation").select("*").eq("agent_id", agent_id).execute()
            row = result.data[0] if result.data else None

            if row:
                total = row["total_tasks"] + 1
                successful = row["successful_tasks"] + (1 if success else 0)
                avg_lat = (row["avg_latency_ms"] * (total-1) + latency_ms) / total
                score = (successful/total)*0.6 + max(0, 1-(avg_lat/10000))*0.3 + 0.1
                self._db.table("agent_reputation").update({
                    "total_tasks": total, "successful_tasks": successful,
                    "avg_latency_ms": avg_lat, "score": round(score, 3),
                }).eq("agent_id", agent_id).execute()
            else:
                self._db.table("agent_reputation").insert({
                    "agent_id": agent_id, "total_tasks": 1,
                    "successful_tasks": 1 if success else 0,
                    "avg_latency_ms": latency_ms, "score": 0.8,
                }).execute()
        except Exception as e:
            log.warning("reputation_update_error", error=str(e))

    def get_score(self, agent_id: str) -> float:
        try:
            r = self._db.table("agent_reputation").select("score").eq("agent_id", agent_id).execute()
            return r.data[0]["score"] if r.data else 0.8
        except Exception:
            return 0.8

reputation = ReputationSystem()


# ============================================================
# UltraAgent — advanced/predict_preload.py
# ============================================================
import structlog
log2 = structlog.get_logger()

class PredictPreload:
    """بيتعلم من الأنماط ويجهز النتائج مسبقاً."""

    def run(self) -> dict:
        # في الإصدار الأول: نسجل فقط، التنبؤ في الإصدار القادم
        log2.info("predict_preload_run")
        return {"status": "logged"}

predict_preload = PredictPreload()


# ============================================================
# UltraAgent — advanced/gossip.py
# ============================================================
import os, structlog
from supabase import create_client
log3 = structlog.get_logger()

class GossipProtocol:
    """الـ agents بتشارك ما تعلمته مع بعض."""

    def __init__(self):
        self._db = create_client(os.getenv("SUPABASE_URL",""), os.getenv("SUPABASE_KEY",""))

    def share(self, agent_type: str, pattern: str, insight: str, score: float = 0.7) -> None:
        try:
            self._db.table("gossip").insert({
                "agent_type": agent_type,
                "context_pattern": pattern,
                "learned_insight": insight,
                "score": score,
            }).execute()
        except Exception as e:
            log3.warning("gossip_share_error", error=str(e))

    def learn(self, agent_type: str, context: str) -> list[str]:
        try:
            r = self._db.table("gossip")\
                .select("learned_insight")\
                .eq("agent_type", agent_type)\
                .gte("score", 0.5)\
                .limit(5)\
                .execute()
            return [row["learned_insight"] for row in (r.data or [])]
        except Exception:
            return []

gossip = GossipProtocol()
