from __future__ import annotations

from typing import Optional

from oko.dashboard.core.repository import DashboardRepository
from oko.dashboard.core.schemas import EventListPage, EventRow, StatsRow

# Допустимые значения фильтра типа
VALID_TYPES = {"error", "http_error", "log", "unhandled"}
DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class DashboardService:
    """
    Бизнес-логика Dashboard layer.

    Получает данные из Repository, собирает схемы для шаблонов.
    Не делает I/O напрямую — только через Repository.
    """

    def __init__(self, repository: DashboardRepository) -> None:
        self._repo = repository

    def get_events_page(
        self,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        event_type: Optional[str] = None,
    ) -> EventListPage:
        """
        Собрать данные для страницы списка событий.

        Валидирует и нормализует параметры фильтрации.
        """
        # Нормализация параметров
        limit = max(1, min(limit, MAX_LIMIT))
        offset = max(0, offset)
        if event_type and event_type not in VALID_TYPES:
            event_type = None

        # Данные
        raw_events = self._repo.get_events(
            limit=limit,
            offset=offset,
            event_type=event_type,
        )
        total = self._repo.count_events(event_type)
        stats = self._get_stats()

        return EventListPage(
            events=[EventRow.from_dict(e) for e in raw_events],
            stats=stats,
            total=total,
            limit=limit,
            offset=offset,
            filter_type=event_type,
        )

    def get_event_detail(self, event_id: int) -> Optional[EventRow]:
        """Получить одно событие для детального просмотра."""
        raw = self._repo.get_event(event_id)
        if raw is None:
            return None
        return EventRow.from_dict(raw)

    def _get_stats(self) -> StatsRow:
        raw = self._repo.get_stats()
        total = raw.pop("total", 0)
        return StatsRow(total=total, by_type=raw)