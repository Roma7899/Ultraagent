# ============================================================
# UltraAgent — core/orchestrator.py
# الـ LangGraph StatefulGraph اللي بيربط كل حاجة
# ============================================================

import structlog
from langgraph.graph import StateGraph, END

from .state import AgentState
from llm.fallback_chain import fallback_chain, FallbackExhausted
from memory.memory_router import memory_router
from agents.research_agent import research_agent
from agents.code_agent import code_agent
from agents.automation_agent import automation_agent
from agents.file_agent import file_agent
from agents.spawner import spawner
from advanced.guardrails import guardrails

log = structlog.get_logger()


# ── Node Functions ──────────────────────────────────────────

def receive_task(state: AgentState) -> AgentState:
    """بيستقبل المهمة ويجيب الـ memory context."""
    log.info("node_receive_task", task=state.task[:80])

    ctx = memory_router.get_context(
        chat_id=state.metadata.get("chat_id", "default"),
        query=state.task,
    )
    state.memory_context = ctx["long_term_context"]
    state.messages = ctx["session_messages"] or []
    state.add_message("user", state.task)
    return state


def plan(state: AgentState) -> AgentState:
    """NIM بيولد خطة خطوة بخطوة."""
    memory_summary = "\n".join(state.memory_context) if state.memory_context else "لا يوجد"

    prompt = f"""أنت orchestrator ذكي. المستخدم طلب:
"{state.task}"

ذكريات ذات صلة:
{memory_summary}

الـ agents المتاحة:
- research_agent: للبحث على الويب
- code_agent: لكتابة وتنفيذ كود Python
- automation_agent: لـ HTTP calls وwebhooks
- file_agent: لرفع وقراءة الملفات
- dynamic_agent: لأي مهمة أخرى

اكتب خطة تنفيذ كـ list مرقمة. كل سطر: [agent_name]: [وصف المهمة]
مثال:
1. research_agent: ابحث عن أحدث أخبار الذكاء الاصطناعي
2. code_agent: اكتب كود يلخص النتائج"""

    try:
        plan_text, model = fallback_chain.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        state.metadata["planning_model"] = model

        # Parse الخطة
        lines = [l.strip() for l in plan_text.strip().split("\n") if l.strip()]
        steps = []
        for line in lines:
            # إزالة الأرقام في البداية
            if ". " in line:
                line = line.split(". ", 1)[1]
            steps.append(line)

        state.plan = steps[:5]  # max 5 خطوات
        log.info("node_plan", steps=state.plan)

    except FallbackExhausted:
        # fallback: خطوة واحدة بـ dynamic agent
        state.plan = [f"dynamic_agent: {state.task}"]

    return state


def route(state: AgentState) -> AgentState:
    """بيحدد الـ agent المناسب للخطوة الحالية."""
    step = state.next_step()
    if step:
        state.metadata["current_agent_task"] = step
        log.info("node_route", step=step)
    return state


def execute(state: AgentState) -> AgentState:
    """بينفذ الخطوة الحالية."""
    step = state.metadata.get("current_agent_task", "")
    if not step:
        return state

    # تحديد الـ agent
    agent_name = "dynamic_agent"
    task_description = step

    for name in ["research_agent", "code_agent", "automation_agent", "file_agent"]:
        if name in step.lower():
            agent_name = name
            if ": " in step:
                task_description = step.split(": ", 1)[1]
            break

    log.info("node_execute", agent=agent_name, task=task_description[:60])

    # Guardrails check
    if not guardrails.check_request():
        state.set_result(agent_name, {"error": "تجاوزت الحد اليومي للطلبات"})
        return state

    # تنفيذ
    if agent_name == "research_agent":
        result = research_agent.run(task_description)
    elif agent_name == "code_agent":
        result = code_agent.run(task_description)
    elif agent_name == "automation_agent":
        result = automation_agent.run(task_description)
    elif agent_name == "file_agent":
        result = file_agent.run(task_description)
    else:
        dynamic = spawner.spawn(task_description)
        result = dynamic.run(task_description)

    state.set_result(agent_name, result.output if result.success else {"error": result.error})
    state.metadata.setdefault("models_used", []).append(result.model_used)

    return state


def check_result(state: AgentState) -> AgentState:
    """بيتحقق من النتيجة ويقرر الخطوة الجاية."""
    log.info("node_check_result", done=state.is_done())
    return state


def finalize(state: AgentState) -> AgentState:
    """بيجمع كل النتائج ويكتب الرد النهائي."""
    results_summary = "\n".join([
        f"- {agent}: {str(output)[:300]}"
        for agent, output in state.results.items()
    ])

    prompt = f"""المهمة الأصلية: {state.task}

نتائج الـ agents:
{results_summary}

اكتب رداً نهائياً للمستخدم بالعربية يلخص ما تم بشكل واضح ومفيد."""

    try:
        final_response, _ = fallback_chain.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
    except FallbackExhausted:
        final_response = f"تم تنفيذ المهمة. النتائج:\n{results_summary}"

    state.add_message("assistant", final_response)

    # حفظ في الذاكرة
    memory_router.save(
        chat_id=state.metadata.get("chat_id", "default"),
        role="assistant",
        content=final_response,
        importance=0.5,
        source="orchestrator",
    )

    state.metadata["final_response"] = final_response
    log.info("node_finalize", response_length=len(final_response))
    return state


# ── Conditional Edges ───────────────────────────────────────

def should_continue(state: AgentState) -> str:
    if state.awaiting_human:
        return "human_checkpoint"
    if state.is_done():
        return "finalize"
    return "route"


# ── Build Graph ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("receive_task", receive_task)
    graph.add_node("plan", plan)
    graph.add_node("route", route)
    graph.add_node("execute", execute)
    graph.add_node("check_result", check_result)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("receive_task")
    graph.add_edge("receive_task", "plan")
    graph.add_edge("plan", "route")
    graph.add_edge("route", "execute")
    graph.add_edge("execute", "check_result")
    graph.add_conditional_edges("check_result", should_continue, {
        "route": "route",
        "finalize": "finalize",
        "human_checkpoint": "finalize",  # simplified
    })
    graph.add_edge("finalize", END)

    return graph.compile()


# Compiled graph
orchestrator = build_graph()


def run_task(task: str, chat_id: str = "default") -> str:
    """Helper function لتشغيل مهمة وإرجاع الرد."""
    initial_state = AgentState(
        task=task,
        metadata={"chat_id": chat_id},
    )
    final_state = orchestrator.invoke(initial_state)
    return final_state.metadata.get("final_response", "عذراً، حدث خطأ.")
