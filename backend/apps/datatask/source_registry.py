from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypedDict


class ExecuteTaskResult(TypedDict):
    ok: bool
    msg: str
    data: Any | None


RuntimeConfig = dict[str, Any] | None
ChangedFields = set[str]


def normalize_execute_result(raw_result: Any) -> ExecuteTaskResult:
    """规范化来源模块执行返回结构，确保任务中心只消费统一 envelope。"""

    if isinstance(raw_result, dict):
        return {
            'ok': bool(raw_result.get('ok', False)),
            'msg': str(raw_result.get('msg') or ''),
            'data': raw_result.get('data'),
        }
    return {
        'ok': False,
        'msg': '来源模块返回结构无效',
        'data': None,
    }


@dataclass(frozen=True)
class SourceHandler:
    """任务来源处理器协议。

    由业务模块注册到 datatask，向平台内核暴露“加载来源对象、同步平台镜像、
    执行任务、实例归一化”等能力，避免平台内核反向依赖业务模块内部实现。
    """

    load_source_record: Callable[[int], Any | None]
    sync_source_task: Callable[[Any], Any]
    sync_platform_snapshot: Callable[[Any, ChangedFields, str], None]
    execute_task: Callable[[Any, Any, str, str, RuntimeConfig], ExecuteTaskResult | dict[str, Any]]
    normalize_task_instance: Callable[[Any], Any] | None = None
    cleanup_stale_instances: Callable[[], list[str]] | None = None


_SOURCE_HANDLERS: dict[str, SourceHandler] = {}


def register_source_handler(source_module: str, handler: SourceHandler) -> None:
    _SOURCE_HANDLERS[source_module] = handler


def get_source_handler(source_module: str) -> SourceHandler | None:
    return _SOURCE_HANDLERS.get(source_module)
