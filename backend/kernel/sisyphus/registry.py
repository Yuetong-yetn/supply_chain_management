"""Agent 注册中心。"""

from typing import Any
from kernel.common.base_agent import BaseAgent


class AgentRegistry:
    """Agent 注册与发现中心。"""

    def __init__(self):
        self._entries: dict[str, dict[str, Any]] = {}

    def register(self, agent: BaseAgent) -> None:
        self._entries[agent.info.name] = {
            "agent": agent,
            "info": agent.info,
            "status": "registered",
        }

    def get(self, name: str) -> BaseAgent | None:
        entry = self._entries.get(name)
        return entry["agent"] if entry else None

    def list(self) -> list[dict[str, Any]]:
        return [
            {"name": v["info"].name, "description": v["info"].description, "status": v["status"]}
            for v in self._entries.values()
        ]
