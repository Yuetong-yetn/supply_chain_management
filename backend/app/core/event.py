"""事件总线 — 转发 kernel.common.event，保证全局单例 event_bus 唯一。"""

from kernel.common.event import Event, EventBus, event_bus

__all__ = ["Event", "EventBus", "event_bus"]
