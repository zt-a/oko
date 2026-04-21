from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class EventRow:
    """Одно событие для списка."""
    id: int
    type: str
    message: str
    stack: str
    context: Dict[str, Any]
    timestamp: float
    fingerprint: str

    @property
    def dt(self) -> str:
        """Форматированное время для отображения."""
        return datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def status_code(self) -> Optional[int]:
        return self.context.get("status_code")

    @property
    def method(self) -> str:
        return self.context.get("method", "")

    @property
    def path(self) -> str:
        return self.context.get("path", "")

    @property
    def project(self) -> str:
        return self.context.get("project", "")

    @property
    def environment(self) -> str:
        return self.context.get("environment", "")

    @property
    def has_stack(self) -> bool:
        return bool(self.stack.strip())

    @property
    def type_label(self) -> str:
        """CSS класс для цвета по типу события."""
        if self.type == "http_error":
            sc = self.status_code or 0
            if sc >= 500:
                return "error"
            return "warning"
        if self.type == "error":
            return "error"
        if self.type == "log":
            return "info"
        return "default"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EventRow":
        return cls(
            id=d["id"],
            type=d["type"],
            message=d["message"],
            stack=d.get("stack", ""),
            context=d.get("context", {}),
            timestamp=d["timestamp"],
            fingerprint=d.get("fingerprint", ""),
        )


@dataclass
class StatsRow:
    """Статистика по типам событий."""
    total: int
    by_type: Dict[str, int] = field(default_factory=dict)

    @property
    def errors(self) -> int:
        return self.by_type.get("error", 0)

    @property
    def http_errors(self) -> int:
        return self.by_type.get("http_error", 0)

    @property
    def logs(self) -> int:
        return self.by_type.get("log", 0)


@dataclass
class EventListPage:
    """Данные для страницы списка событий."""
    events: List[EventRow]
    stats: StatsRow
    total: int
    limit: int
    offset: int
    filter_type: Optional[str]

    @property
    def has_next(self) -> bool:
        return self.offset + self.limit < self.total

    @property
    def has_prev(self) -> bool:
        return self.offset > 0

    @property
    def next_offset(self) -> int:
        return self.offset + self.limit

    @property
    def prev_offset(self) -> int:
        return max(0, self.offset - self.limit)

    @property
    def page_number(self) -> int:
        return (self.offset // self.limit) + 1

    @property
    def total_pages(self) -> int:
        if self.limit == 0:
            return 1
        return max(1, -(-self.total // self.limit))  # ceil division