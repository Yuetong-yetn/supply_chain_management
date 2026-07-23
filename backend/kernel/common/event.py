"""进程内事件总线 — 跨 Agent 通信的唯一途径。"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Agent 间传递的事件"""

    type: str
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str = ""


class EventBus:
    """进程内发布/订阅总线。

    支持同步订阅（发布者等待所有订阅者处理完毕）。
    一个事件类型可以有多个订阅者，按注册顺序执行。
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅一个事件类型。handler 接收 Event 参数。"""
        self._subscribers[event_type].append(handler)
        logger.debug("[EventBus] SUBSCRIBE %s <- %s", event_type, handler.__name__)

    def publish(self, event: Event) -> None:
        """发布事件，同步调用所有订阅者。"""
        logger.info("[EventBus] %s >> %s", event.source, event.type)
        for handler in self._subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as e:
                logger.exception(
                    "Handler %s failed on %s: %s",
                    handler.__name__, event.type, e,
                )
                raise

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅。"""
        self._subscribers[event_type].remove(handler)


# 全局单例
event_bus = EventBus()
