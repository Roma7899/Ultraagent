# UltraAgent 🤖
> AI Agent مجاني 100% على السحابة | Python + LangGraph + NVIDIA NIM

---

## 📋 قبل ما تبدأ — اجمع الحاجات دي

| الحاجة | من فين | وقت التسجيل |
|--------|--------|-------------|
| NVIDIA API Key | [build.nvidia.com](https://build.nvidia.com) | 2 دقيقة |
| Supabase URL + Key | [supabase.com](https://supabase.com) | 3 دقائق |
| Upstash Redis URL + Password | [upstash.com](https://upstash.com) | 2 دقيقة |
| Telegram Bot Token | @BotFather على Telegram | 1 دقيقة |
| Telegram Chat ID | @userinfobot على Telegram | 1 دقيقة |
| Tavily API Key | [tavily.com](https://tavily.com) | 2 دقيقة |
| E2B API Key | [e2b.dev](https://e2b.dev) | 2 دقيقة |

---

## 🚀 خطوات الرفع على السحابة

---

### الخطوة 1 — Supabase (قاعدة البيانات)

1. اذهب إلى [supabase.com](https://supabase.com) → **Start your project** → سجل بـ GitHub
2. اضغط **New Project** → اختر اسم وكلمة سر → اضغط **Create new project**
3. انتظر ~2 دقيقة لحد ما يخلص الإعداد
4. اذهب إلى **Settings** (أيقونة الترس) → **API**
5. انسخ:
   - `Project URL` → هيبقى `SUPABASE_URL`
   - `anon public` key → هيبقى `SUPABASE_KEY`
6. اذهب إلى **SQL Editor** (في الـ sidebar) → **New query**
7. افتح ملف `supabase_schema.sql` من المشروع، انسخ محتواه كله والصقه في الـ editor
8. اضغط **Run** — المفروض تشوف رسالة "Success"

**⚠️ خطوة إضافية مهمة — Supabase Storage:**
1. اذهب إلى **Storage** في الـ sidebar
2. اضغط **New bucket**
3. اكتب الاسم: `ultraagent-files`
4. اختر **Public** → اضغط **Create bucket**

---

### الخطوة 2 — Upstash Redis

1. اذهب إلى [upstash.com](https://upstash.com) → سجل مجاناً
2. اضغط **Create Database**
3. اختر **Redis** → اكتب اسم → اختر أقرب region ليك → اضغط **Create**
4. بعد الإنشاء، اضغط على الـ database → اذهب إلى تبويب **Details**
5. انسخ:
   - `Endpoint` (بيبدأ بـ `redis://`) → هيبقى `REDIS_URL`
   - `Password` → هيبقى `REDIS_PASSWORD`

---

### الخطوة 3 — NVIDIA NIM

1. اذهب إلى [build.nvidia.com](https://build.nvidia.com) → **Sign In** أو **Join**
2. بعد تسجيل الدخول، اضغط على اسمك في الأعلى → **API Keys**
3. اضغط **Generate API Key**
4. انسخ الـ key (بيبدأ بـ `nvapi-`) → هيبقى `NVIDIA_API_KEY`

---

### الخطوة 4 — Telegram Bot

**عشان تاخد الـ Token:**
1. افتح Telegram وابحث عن **@BotFather**
2. ابعت `/newbot`
3. اكتب اسم للـ bot (مثلاً: My Ultra Agent)
4. اكتب username للـ bot (لازم ينتهي بـ `bot`، مثلاً: `myultraagent_bot`)
5. هيبعتلك الـ Token — انسخه → هيبقى `TELEGRAM_BOT_TOKEN`

**عشان تاخد الـ Chat ID بتاعك:**
1. ابحث عن **@userinfobot** على Telegram
2. ابعت أي رسالة
3. هيرد بـ id بتاعك — انسخه → هيبقى `TELEGRAM_ADMIN_CHAT_ID`

---

### الخطوة 5 — Tavily و E2B

**Tavily:**
1. اذهب إلى [tavily.com](https://tavily.com) → **Get Started**
2. سجل → اذهب إلى **Dashboard** → انسخ الـ API Key → هيبقى `TAVILY_API_KEY`

**E2B:**
1. اذهب إلى [e2b.dev](https://e2b.dev) → **Sign up**
2. بعد التسجيل اذهب إلى [e2b.dev/dashboard](https://e2b.dev/dashboard) → **API Keys**
3. انسخ الـ key → هيبقى `E2B_API_KEY`

---

### الخطوة 6 — GitHub

1. اذهب إلى [github.com](https://github.com) → سجل لو مش عندك account
2. اضغط **New repository** → اكتب اسم `ultraagent` → اختر **Private** → اضغط **Create**
3. على جهازك، افتح terminal في مجلد المشروع ونفذ:

```bash
git init
git add .
git commit -m "UltraAgent v1.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ultraagent.git
git push -u origin main
```

> ⚠️ **مهم جداً:** تأكد إن ملف `.env` موجود في `.gitignore` ومش اترفعش على GitHub أبداً!

---

### الخطوة 7 — Render (التشغيل على السحابة)

1. اذهب إلى [render.com](https://render.com) → **Get Started for Free**
2. سجل بـ GitHub عشان يتربط تلقائياً
3. اضغط **New** → **Blueprint**
4. اختر الـ repo `ultraagent` من القائمة → اضغط **Connect**
5. Render هيقرأ `render.yaml` ويعمل 5 services تلقائياً:
   - `ultraagent-api` — Web Service (REST API)
   - `ultraagent-bot` — Worker (Telegram bot يشتغل 24/7)
   - `dreaming-mode` — Cron (كل يوم 02:00 UTC)
   - `self-improvement` — Cron (كل أحد 03:00 UTC)
   - `predict-preload` — Cron (كل 6 ساعات)

**⚠️ خطوة إضافية مهمة — إضافة Environment Variables:**

الطريقة الأسهل: اعمل **Environment Group** مرة واحدة وارتبطه بكل الـ services:

1. في Render Dashboard → اضغط **Environment Groups** (في الـ sidebar) → **New Environment Group**
2. اكتب اسم: `ultraagent-env`
3. أضف كل الـ variables دي:

```
NVIDIA_API_KEY         = nvapi-xxxx
SUPABASE_URL           = https://xxxx.supabase.co
SUPABASE_KEY           = eyJxxx
REDIS_URL              = redis://xxxx.upstash.io:6379
REDIS_PASSWORD         = xxxx
TELEGRAM_BOT_TOKEN     = xxxx:xxxx
TELEGRAM_ADMIN_CHAT_ID = 123456789
TAVILY_API_KEY         = tvly-xxxx
E2B_API_KEY            = xxxx
MAX_DAILY_REQUESTS     = 500
ENVIRONMENT            = production
LOG_LEVEL              = INFO
```

4. اضغط **Save**
5. اذهب لكل service → **Environment** → **Link Environment Group** → اختر `ultraagent-env`

---

### الخطوة 8 — اختبار النظام

بعد ما Render يخلص الـ deploy (بياخد 3-5 دقائق):

```
على Telegram:
/start                              → المفروض الـ bot يرد بالترحيب
"ابحث عن أخبار الذكاء الاصطناعي"  → Research Agent
"اكتب كود Python يحسب فيبوناتشي"  → Code Agent
"تذكر اسمي [اسمك]"                → Long-term Memory
"ما اسمي؟" (في محادثة جديدة)      → بيسترجع من الذاكرة
```

على REST API:
```
GET  https://ultraagent-api.onrender.com/      → health check
POST https://ultraagent-api.onrender.com/task  → تنفيذ مهمة
```

---

### الخطوة 9 — بعد أسبوع (Optimization)

راجع في Supabase Dashboard → **Table Editor**:
- `agent_reputation` — أي agent عنده score منخفض؟
- `prompt_versions` — أي نسخة prompt أفضل؟
- `gossip` — إيه اللي تعلمه النظام لوحده؟
- `task_history` — إيه المهام اللي بتتكرر؟

---

## 🔧 Troubleshooting — حل المشاكل الشائعة

### ❌ الـ Bot مش بيرد
- تأكد إن `TELEGRAM_BOT_TOKEN` صح في Render
- اذهب إلى Render → `ultraagent-bot` (Worker) → **Logs** وشوف الـ error
- تأكد إن الـ Worker status بيقول **Running** مش **Failed**

### ❌ خطأ في Supabase connection
- تأكد إن `SUPABASE_URL` بيبدأ بـ `https://` وينتهي بـ `.supabase.co`
- تأكد إنك شغّلت الـ SQL schema كاملاً
- في Supabase → **Database** → **Extensions** → تأكد إن `vector` مفعّل

### ❌ خطأ في Redis connection
- تأكد إن `REDIS_URL` بيبدأ بـ `redis://` أو `rediss://`
- في Upstash Dashboard تأكد إن الـ database status = **Active**

### ❌ الـ Web API بطيء أول request
- ده طبيعي تماماً على Render free tier
- الـ service بينام بعد 15 دقيقة من غير استخدام
- أول request بعد النوم بياخد ~30 ثانية يصحى
- الـ Telegram bot مش بيتأثر لأنه Worker مش Web service ✅

### ❌ NVIDIA NIM بيرفض الـ requests
- تأكد إن الـ key بيبدأ بـ `nvapi-`
- الـ free tier عنده حد يومي — الـ guardrails بتتعامل معاه تلقائياً
- لو وصلت الحد، انتظر لحد اليوم التالي

### ❌ Supabase project اتوقف
- Supabase بيوقف الـ project لو مفيش استخدام 7 أيام
- الحل: اذهب إلى supabase.com وافتح الـ project يصحى تلقائياً
- أو فعّل أي request بسيط كل بضعة أيام

---

## 📁 هيكل الملفات

```
ultraagent/
├── main.py                    # entry point للـ FastAPI
├── requirements.txt           # كل الـ dependencies
├── render.yaml                # deployment config (5 services)
├── supabase_schema.sql        # SQL لإنشاء الجداول والـ functions
├── .env.example               # template للـ environment variables
├── .gitignore                 # يحمي .env من GitHub
│
├── core/
│   ├── state.py               # AgentState dataclass
│   └── orchestrator.py        # LangGraph graph كامل
│
├── llm/
│   ├── nim_client.py          # NVIDIA NIM client
│   └── fallback_chain.py      # 4 موديلات fallback تلقائي
│
├── agents/
│   ├── base_agent.py          # parent class لكل الـ agents
│   ├── research_agent.py      # Tavily web search
│   ├── code_agent.py          # E2B sandbox execution
│   ├── automation_agent.py    # HTTP/webhook calls
│   ├── file_agent.py          # Supabase storage
│   └── spawner.py             # dynamic agent creator
│
├── memory/
│   ├── short_term.py          # Redis session memory
│   ├── long_term.py           # Supabase + pgvector
│   └── memory_router.py       # يوجه الذاكرة للمكان الصح
│
├── advanced/
│   ├── guardrails.py          # حماية من التكاليف المفرطة
│   ├── self_improvement.py    # weekly prompt optimizer
│   └── reputation_gossip.py  # agent scoring + knowledge sharing
│
├── interfaces/
│   ├── telegram_bot.py        # Telegram bot interface
│   └── rest_api.py            # FastAPI REST endpoints
│
├── scheduler/
│   └── cron_tasks.py          # dreaming + self-improve + predict
│
└── utils/
    ├── logger.py              # structured logging
    └── human_checkpoint.py    # Telegram approval للأفعال الخطيرة
```

---

## 💰 التكلفة الشهرية: $0

| الخدمة | الـ Free Tier |
|--------|--------------|
| Render | Web + Worker + 3 Crons مجاناً |
| Supabase | 500MB database + Storage مجاناً |
| Upstash Redis | 10,000 commands/يوم مجاناً |
| NVIDIA NIM | حد يومي مجاني كافي للاستخدام الشخصي |
| Tavily | 1,000 بحث/شهر مجاناً |
| E2B | 100 ساعة sandbox/شهر مجاناً |
| Telegram | مجاني بالكامل |

---

## ▶️ استكمال البناء بعد توقف

لو احتجت تكمل من نقطة معينة، ابعت هذا الـ prompt لأي AI:

```
أنا بابني UltraAgent — AI Agent مجاني كامل على السحابة.
توقفت عند: [اسم الملف الأخير اللي اتبنى]
كمل من: [اسم الملف التالي في Build Order]
[الصق ملف AI_AGENT_BLUEPRINT.md كاملاً]
```
