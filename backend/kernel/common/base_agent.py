"""Agent 基类 — 所有业务 Agent 必须继承此类。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from fastapi import APIRouter


@dataclass
class AgentInfo:
    """Agent 注册元信息"""

    name: str
    description: str
    version: str = "1.0.0"
    dependencies: list[str] = field(default_factory=list)
    owns_tables: list[str] = field(default_factory=list)


class BaseAgent(ABC):
    """所有业务 Agent 必须继承的基类。

    子类必须实现:
      - info: AgentInfo 属性
      - register_routes(): 返回本 Agent 的 APIRouter 列表
      - register_subscriptions(): 返回 {event_type: handler} 映射
    """

    @property
    @abstractmethod
    def info(self) -> AgentInfo:
        """返回 Agent 注册信息"""
        ...

    @abstractmethod
    def register_routes(self) -> list[APIRouter]:
        """返回本 Agent 的所有 FastAPI APIRouter"""
        ...

    @abstractmethod
    def register_subscriptions(self) -> dict[str, Callable]:
        """返回 {event_type: handler} 订阅映射"""
        ...

    def on_startup(self):
        """Agent 启动时的初始化逻辑（可选重写）"""
        ...

    def on_shutdown(self):
        """Agent 关闭时的清理逻辑（可选重写）"""
        ...
