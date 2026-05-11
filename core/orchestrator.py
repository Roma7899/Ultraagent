# ============================================================
# UltraAgent — core/orchestrator.py
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


def receive_task(state: AgentState) -> dict:
    chat_id = (state.get("metadata") or {}).get("chat_id", "default")
    task = state.get("task", "")
    log.info("node_receive_task", task=task[:80])

    ctx = memory_router.get_context(chat_id=chat_id, query=task)
    messages = ctx.get("session_messages") or []
    messages.append({"role": "user", "content": task})

    return {
        "memory_context": ctx.get("long_term_context", []),
        "messages": messages,
    }


def planning(state: AgentState) -> dict:
    task = state.get("task", "")
    memory_context = state.get("memory_context", [])
    memory_summary = "\n".join(memory_context) if memory_context else "لا يوجد"

    prompt = f"""أنت orchestrator ذكي. المستخدم طلب:
"{task}"

ذكريات ذات صلة:
{memory_summary}

الـ agents المتاحة:
- research_agent: للبحث على الويب
- code_agent: لكتابة وتنفيذ كود Python
- automation_agent: لـ HTTP calls وwebhooks
- file_agent: لرفع وقراءة الملفات
- dynamic_agent: لأي مهمة أخرى

اكتب خطة تنفيذ كـ list مرقمة. كل سطر: [agent_name]: [وصف المهمة]"""

    try:
        plan_text, model = fallback_chain.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        lines = [l.strip() for l in plan_text.strip().split("\n") if l.strip()]
        steps = []
        for line in lines:
            if ". " in line:
                line = line.split(". ", 1)[1]
            steps.append(line)
        plan_steps = steps[:5]
    except FallbackExhausted:
        plan_steps = [f"dynamic_agent: {task}"]

    meta = dict(state.get("metadata") or {})
    meta["planning_model"] = model if 'model' in dir() else ""
    return {"plan": plan_steps, "current_step": 0, "metadata": meta}


def routing(state: AgentState) -> dict:
    plan_steps = state.get("plan", [])
    current_step = state.get("current_step", 0)

    if current_step < len(plan_steps):
        step = plan_steps[current_step]
        meta = dict(state.get("metadata") or {})
        meta["current_agent_task"] = step
        log.info("node_route", step=step)
        return {"current_step": current_step + 1, "metadata": meta}
    return {}


def executing(state: AgentState) -> dict:
    meta = state.get("metadata") or {}
    step = meta.get("current_agent_task", "")
    if not step:
        return {}

    agent_name = "dynamic_agent"
    task_description = step
    for name in ["research_agent", "code_agent", "automation_agent", "file_agent"]:
        if name in step.lower():
            agent_name = name
            if ": " in step:
                task_description = step.split(": ", 1)[1]
            break

    log.info("node_execute", agent=agent_name, task=task_description[:60])

    if not guardrails.check_request():
        results = dict(state.get("results") or {})
        results[agent_name] = {"error": "تجاوزت الحد اليومي"}
        return {"results": results}

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

    results = dict(state.get("results") or {})
    results[agent_name] = result.output if result.success else {"error": result.error}
    return {"results": results}


def check_result(state: AgentState) -> dict:
    return {}


def finalize(state: AgentState) -> dict:
    task = state.get("task", "")
    results = state.get("results") or {}
    meta = dict(state.get("metadata") or {})
    chat_id = meta.get("chat_id", "default")

    results_summary = "\n".join([
        f"- {agent}: {str(output)[:300]}"
        for agent, output in results.items()
    ])

    prompt = f"""المهمة الأصلية: {task}

نتائج الـ agents:
{results_summary}

اكتب رداً نهائياً للمستخدم بالعربية يلخص ما تم بشكل واضح ومفيد."""

    try:
        final_response, _ = fallback_chain.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
    except FallbackExhausted:
        final_response = f"تم تنفيذ المهمة.\n{results_summary}"

    messages = list(state.get("messages") or [])
    messages.append({"role": "assistant", "content": final_response})

    memory_router.save(
        chat_id=chat_id,
        role="assistant",
        content=final_response,
        importance=0.5,
        source="orchestrator",
    )

    meta["final_response"] = final_response
    return {"messages": messages, "metadata": meta}


def should_continue(state: AgentState) -> str:
    if state.get("awaiting_human"):
        return "finalize"
    plan_steps = state.get("plan", [])
    current_step = state.get("current_step", 0)
    if current_step >= len(plan_steps):
        return "finalize"
    return "route"


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("receive_task", receive_task)
    graph.add_node("planning", planning)
    graph.add_node("routing", routing)
    graph.add_node("executing", executing)
    graph.add_node("check_result", check_result)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("receive_task")
    graph.add_edge("receive_task", "planning")
    graph.add_edge("planning", "routing")
    graph.add_edge("routing", "executing")
    graph.add_edge("executing", "check_result")
    graph.add_conditional_edges("check_result", should_continue, {
        "route": "routing",
        "finalize": "finalize",
    })
    graph.add_edge("finalize", END)
    return graph.compile()


orchestrator = build_graph()


def run_task(task: str, chat_id: str = "default") -> str:
    initial_state = {"task": task, "messages": [], "plan": [], "current_step": 0, "results": {}, "active_agents": [], "memory_context": [], "awaiting_human": False, "error_count": 0, "spawned_agents": [], "metadata": {"chat_id": chat_id}}
    final_state = orchestrator.invoke(initial_state)
    return (final_state.get("metadata") or {}).get("final_response", "عذراً، حدث خطأ.")
