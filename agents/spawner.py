# ============================================================
# UltraAgent — agents/spawner.py
# بيولد agents جديدة at runtime لو مفيش agent مناسب
# ============================================================

import structlog
from llm.fallback_chain import fallback_chain
from .base_agent import BaseAgent, AgentResult

log = structlog.get_logger()


class DynamicAgent(BaseAgent):
    """Agent متولد ديناميكياً بـ system prompt مخصص."""

    def __init__(self, agent_id: str, system_prompt: str):
        super().__init__(agent_id)
        self._system_prompt = system_prompt

    def _execute(self, task: str, context: dict) -> AgentResult:
        try:
            text, model = fallback_chain.complete(
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {"role": "user", "content": task},
                ],
                max_tokens=800,
            )
            return AgentResult(success=True, output=text, model_used=model)
        except Exception as e:
            return AgentResult(success=False, output=None, error=str(e))


class AgentSpawner:
    """
    بيحلل المهمة ويولد agent مناسب لها.
    """
    _spawned: dict[str, DynamicAgent] = {}

    def spawn(self, task: str) -> DynamicAgent:
        """بيولد dynamic agent للمهمة."""
        # اطلب من NIM يصمم الـ agent
        design_prompt = f"""المهمة التالية محتاجة agent متخصص:
"{task}"

صمم system prompt مناسب لهذا الـ agent. كن محدداً بشأن:
- ما يفعله هذا الـ agent
- أسلوب الرد
- القيود والحدود

اكتب system prompt فقط بدون مقدمة."""

        try:
            system_prompt, _ = fallback_chain.complete(
                messages=[{"role": "user", "content": design_prompt}],
                max_tokens=400,
                temperature=0.5,
            )
        except Exception:
            system_prompt = f"أنت agent متخصص في: {task}. أجب بدقة واحترافية."

        agent_id = f"dynamic_{len(self._spawned) + 1}"
        agent = DynamicAgent(agent_id, system_prompt)
        self._spawned[agent_id] = agent

        log.info("agent_spawned", agent_id=agent_id, task_preview=task[:60])
        return agent

    def get_or_spawn(self, task_type: str, task: str) -> DynamicAgent:
        """بيرجع agent موجود أو بيولد واحد جديد."""
        if task_type in self._spawned:
            return self._spawned[task_type]
        return self.spawn(task)


spawner = AgentSpawner()
