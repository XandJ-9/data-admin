from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class SourceHandler:
    """任务来源处理器协议。

    由业务模块注册到 datatask，向平台内核暴露“加载来源对象、同步平台镜像、
    执行任务、实例归一化”等能力，避免平台内核反向依赖业务模块内部实现。
    """

    load_source_record: Callable[[int], Any | None]
    sync_source_task: Callable[[Any], Any]
    sync_platform_snapshot: Callable[[Any, set[str], str], None]
    execute_task: Callable[[Any, Any, str, str, dict | None], dict]
    normalize_task_instance: Callable[[Any], Any] | None = None
    cleanup_stale_instances: Callable[[], list[str]] | None = None


_SOURCE_HANDLERS: dict[str, SourceHandler] = {}


def register_source_handler(source_module: str, handler: SourceHandler) -> None:
    _SOURCE_HANDLERS[source_module] = handler


def get_source_handler(source_module: str) -> SourceHandler | None:
    return _SOURCE_HANDLERS.get(source_module)
