"""配置管理 — 转发 kernel.common.config，保证 get_settings 单例唯一。"""

from kernel.common.config import Settings, get_settings, BASE_DIR

__all__ = ["Settings", "get_settings", "BASE_DIR"]
