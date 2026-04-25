from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class SourceHandler:
    load_source_record: Callable[[int], Any | None]
    sync_source_task: Callable[[Any], Any]
    sync_platform_snapshot: Callable[[Any, set[str], str], None]
    execute_task: Callable[[Any, Any, str, str, dict | None], dict]


_SOURCE_HANDLERS: dict[str, SourceHandler] = {}


def register_source_handler(source_module: str, handler: SourceHandler) -> None:
    _SOURCE_HANDLERS[source_module] = handler


def get_source_handler(source_module: str) -> SourceHandler | None:
    return _SOURCE_HANDLERS.get(source_module)
