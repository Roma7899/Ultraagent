# UltraAgent — core/state.py
from typing import Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    task: str
    messages: list
    plan: list
    current_step: int
    results: dict
    active_agents: list
    memory_context: list
    awaiting_human: bool
    error_count: int
    spawned_agents: list
    metadata: dict
