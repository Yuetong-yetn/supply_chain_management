"""工作流引擎 — 管理需要多个 Agent 协作的复杂业务流程。"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from kernel.common.event import Event, event_bus


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    name: str
    agent: str
    action: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    name: str
    steps: list[WorkflowStep]


class WorkflowEngine:
    """工作流引擎。

    每个工作流是一个有向无环图（DAG），节点是 Agent 操作，边是事件依赖。
    一个步骤完成后发布事件 → 引擎检查哪些步骤可以进入 → 派发。
    """

    def __init__(self):
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._active: dict[str, dict[str, Any]] = {}

    def define(self, workflow: WorkflowDefinition) -> None:
        self._workflows[workflow.name] = workflow

    def start(self, workflow_name: str, init_data: dict[str, Any]) -> str:
        wf_id = f"wf-{uuid.uuid4().hex[:8]}"
        self._active[wf_id] = {
            "name": workflow_name,
            "status": WorkflowStatus.RUNNING,
            "data": init_data,
            "completed_steps": [],
            "step_results": {},
        }
        wf = self._workflows.get(workflow_name)
        if wf:
            for step in wf.steps:
                if not step.depends_on:
                    self._dispatch_step(wf_id, step)
        return wf_id

    def _dispatch_step(self, wf_id: str, step: WorkflowStep) -> None:
        event_bus.publish(
            Event(
                type=f"workflow.step.{step.action}",
                source="sisyphus",
                data={"workflow_id": wf_id, "step": step.name, "agent": step.agent},
                correlation_id=wf_id,
            )
        )

    def complete_step(self, wf_id: str, step_name: str, result: Any = None) -> None:
        active = self._active.get(wf_id)
        if not active:
            return
        active["completed_steps"].append(step_name)
        if result:
            active["step_results"][step_name] = result
        wf = self._workflows.get(active["name"])
        if wf and all(s.name in active["completed_steps"] for s in wf.steps):
            active["status"] = WorkflowStatus.COMPLETED
