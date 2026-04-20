from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """
    Абстрактный интерфейс для всех Adapters.

    Adapter — входная точка системы.
    Он перехватывает события фреймворка и превращает их в OkoEvent,
    затем передаёт в Core через engine.capture_*().

    Правила:
        - Adapter не пишет в Storage напрямую
        - Adapter не вызывает Connectors
        - Adapter не содержит бизнес-логику
        - Adapter не знает про Pipeline

    Расширение:
        from oko.adapters.base import BaseAdapter

        class MyAdapter(BaseAdapter):
            def install(self, app, engine):
                # подключить middleware к app
                pass
    """

    @abstractmethod
    def install(self, app: Any, engine: Any) -> None:
        """
        Подключить адаптер к приложению.

        Args:
            app:    экземпляр фреймворка (FastAPI, Flask, ...)
            engine: OkoEngine — куда передавать события
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"