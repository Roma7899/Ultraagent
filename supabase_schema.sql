-- ============================================================
-- UltraAgent — Supabase Schema
-- شغّل هذا الـ SQL في Supabase SQL Editor
-- ============================================================

-- 1. تفعيل pgvector (مرة واحدة فقط)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. جدول الذاكرة طويلة المدى
CREATE TABLE IF NOT EXISTS memories (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content       TEXT NOT NULL,
  embedding     VECTOR(1536),
  source        TEXT DEFAULT 'agent',
  importance    FLOAT DEFAULT 0.5,
  consolidated  BOOLEAN DEFAULT FALSE,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  last_accessed TIMESTAMPTZ DEFAULT NOW(),
  access_count  INT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS memories_embedding_idx
  ON memories USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 3. دالة البحث بالتشابه
CREATE OR REPLACE FUNCTION search_memories(
  query_embedding VECTOR(1536),
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID, content TEXT, source TEXT,
  importance FLOAT, similarity FLOAT
)
LANGUAGE SQL STABLE AS $$
  SELECT id, content, source, importance,
         1 - (embedding <=> query_embedding) AS similarity
  FROM memories
  WHERE consolidated = FALSE
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- 4. دالة تحديث الوصول
CREATE OR REPLACE FUNCTION increment_memory_access(memory_id UUID)
RETURNS VOID LANGUAGE SQL AS $$
  UPDATE memories
  SET access_count = access_count + 1,
      last_accessed = NOW()
  WHERE id = memory_id;
$$;

-- 5. جدول أداء الـ agents
CREATE TABLE IF NOT EXISTS agent_reputation (
  agent_id         TEXT PRIMARY KEY,
  total_tasks      INT DEFAULT 0,
  successful_tasks INT DEFAULT 0,
  avg_latency_ms   FLOAT DEFAULT 0,
  last_failure     TEXT,
  score            FLOAT DEFAULT 0.8,
  suspended_until  TIMESTAMPTZ
);

-- 6. جدول تاريخ المهام
CREATE TABLE IF NOT EXISTS task_history (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task        TEXT,
  plan        JSONB,
  result      JSONB,
  success     BOOLEAN,
  model_used  TEXT,
  agent_used  TEXT,
  latency_ms  INT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 7. جدول نسخ الـ prompts
CREATE TABLE IF NOT EXISTS prompt_versions (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_type   TEXT,
  prompt_text  TEXT,
  version      INT DEFAULT 1,
  active       BOOLEAN DEFAULT FALSE,
  traffic_pct  INT DEFAULT 0,
  success_rate FLOAT DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- 8. جدول الـ Gossip
CREATE TABLE IF NOT EXISTS gossip (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_type       TEXT,
  context_pattern  TEXT,
  learned_insight  TEXT,
  use_count        INT DEFAULT 0,
  score            FLOAT DEFAULT 0.5,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- 9. جدول بروفايل المستخدم
CREATE TABLE IF NOT EXISTS user_profile (
  key        TEXT PRIMARY KEY,
  value      JSONB,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
