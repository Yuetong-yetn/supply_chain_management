from collections.abc import Callable
from typing import Any


TASK_REGISTRY: dict[str, Callable[[dict[str, Any]], Any]] = {}
TASK_LOG: list[dict[str, Any]] = []


def register_task(task_name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
    TASK_REGISTRY[task_name] = handler


def enqueue_task(task_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    task = {"task_name": task_name, "payload": payload, "status": "queued"}
    TASK_LOG.append(task)
    return task


def run_task(task_name: str, payload: dict[str, Any]) -> Any:
    handler = TASK_REGISTRY.get(task_name)
    if not handler:
        return {"task_name": task_name, "status": "skipped", "reason": "handler_not_found"}
    return handler(payload)
