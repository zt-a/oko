from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from oko.core.event import OkoEvent


class BaseConnector(ABC):
    """
    Абстрактный интерфейс для всех Connectors.

    Connector — это выход системы (side effect).
    Он получает событие и доставляет его наружу:
        Telegram, Webhook, Discord, Slack и т.д.

    Правила:
        - Connector не изменяет событие
        - Connector не пишет в Storage
        - Connector не вызывает Pipeline
        - Connector не знает про Core

    Расширение:
        from oko.connectors.base import BaseConnector

        class MyConnector(BaseConnector):
            async def send(self, event: OkoEvent) -> None:
                print(event.message)
    """

    @abstractmethod
    async def send(self, event: OkoEvent) -> None:
        """
        Отправить одно событие.

        Реализация должна быть async — даже если внутри синхронный код,
        это позволяет единообразно вызывать все коннекторы.
        """
        ...

    async def send_batch(self, events: List[OkoEvent]) -> None:
        """
        Отправить пачку событий.

        По умолчанию — отправляет по одному.
        Коннектор может переопределить для batch-оптимизации.
        """
        for event in events:
            await self.send(event)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"