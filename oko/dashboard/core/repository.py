from __future__ import annotations

from typing import Any, Dict, List, Optional

from oko.storage.base import BaseStorage


class DashboardRepository:
    """
    Read-only доступ к данным через Storage интерфейс.

    Правило: Dashboard не знает про SQLite напрямую.
    Он работает только через BaseStorage — это позволяет
    использовать любую реализацию хранилища.

    Поток: Storage → Repository → Service → Template
    """

    def __init__(self, storage: BaseStorage) -> None:
        self._storage = storage

    def get_events(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Получить список событий с пагинацией и фильтром."""
        return self._storage.fetch(
            limit=limit,
            offset=offset,
            event_type=event_type,
        )

    def get_event(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получить одно событие по ID."""
        return self._storage.fetch_by_id(event_id)

    def count_events(self, event_type: Optional[str] = None) -> int:
        """Количество событий (с фильтром или всего)."""
        return self._storage.count(event_type)

    def get_stats(self) -> Dict[str, int]:
        """
        Статистика по типам событий.

        Returns:
            {"total": 42, "error": 10, "http_error": 30, "log": 2}
        """
        types = ["error", "http_error", "log", "unhandled"]
        stats = {"total": self._storage.count()}
        for t in types:
            count = self._storage.count(t)
            if count > 0:
                stats[t] = count
        return stats