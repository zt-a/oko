from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseStorage(ABC):
    """
    Абстрактный интерфейс для всех Storage реализаций.

    Storage — source of truth системы.
    Только он пишет в базу данных, никто другой.

    Правила:
        - Storage не вызывает Connectors
        - Storage не знает про Pipeline
        - Storage не знает про Core
        - Dashboard читает только через Storage

    Расширение:
        from oko.storage.base import BaseStorage

        class MyStorage(BaseStorage):
            def save_batch(self, events):
                for e in events:
                    my_db.insert(e.to_dict())

            def fetch(self, limit=100, offset=0):
                return my_db.select(limit=limit, offset=offset)

            def count(self):
                return my_db.count()
    """

    @abstractmethod
    def save_batch(self, events: List[Any]) -> None:
        """
        Сохранить пачку событий.

        Принимает List[OkoEvent] — batch insert обязателен по правилам.
        Не сохраняет по одному на каждый event.
        """
        ...

    @abstractmethod
    def fetch(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Получить события для Dashboard (read-only).

        Args:
            limit:      максимум записей
            offset:     пагинация
            event_type: фильтр по типу ("error", "http_error", ...)

        Returns:
            List[dict] — сериализованные события
        """
        ...

    @abstractmethod
    def count(self, event_type: Optional[str] = None) -> int:
        """Общее количество событий (для Dashboard статистики)."""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"