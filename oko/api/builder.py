from __future__ import annotations

import asyncio
import logging
import threading
from typing import List, Optional

from oko.connectors.base import BaseConnector
from oko.connectors.telegram import TelegramConnector
from oko.core.engine import OkoEngine
from oko.core.event import OkoEvent
from oko.pipeline.processor import OkoPipeline
from oko.storage.base import BaseStorage
from oko.storage.sqlite import SQLiteStorage

logger = logging.getLogger("oko.api.builder")


class OkoBuilder:
    """
    Собирает всю систему OKO из конфига.

    Единственное место где знают про все слои одновременно.
    Реализует Dependency Injection из RULES.md:
        все зависимости передаются явно, не берутся из воздуха.

    Поток сборки:
        1. Storage    — куда сохранять события
        2. Connectors — куда отправлять уведомления
        3. output_handler — связывает Storage + Connectors
        4. Pipeline   — обработка событий перед output
        5. Engine     — ядро, принимает события от Adapters

    Использование:
        builder = OkoBuilder(
            telegram_token="...",
            telegram_chat_id="...",
        )
        engine = builder.build()
    """

    def __init__(
        self,
        # Telegram
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        # Storage
        storage: Optional[BaseStorage] = None,
        db_path: str = "oko.db",
        # Connectors
        connector: Optional[BaseConnector] = None,
        extra_connectors: Optional[List[BaseConnector]] = None,
        # Pipeline
        silence: float = 900.0,
        rate_limit_max: float = 10.0,
        rate_limit_refill: float = 1.0,
        # Enrichment
        project: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        # Engine
        batch_size: int = 10,
        poll_interval: float = 1.0,
    ) -> None:
        # Telegram
        self._telegram_token = telegram_token
        self._telegram_chat_id = telegram_chat_id

        # Storage — кастомный или SQLite по умолчанию
        self._storage = storage or SQLiteStorage(db_path)

        # Connectors
        self._connector = connector
        self._extra_connectors = extra_connectors or []

        # Pipeline
        self._silence = silence
        self._rate_limit_max = rate_limit_max
        self._rate_limit_refill = rate_limit_refill

        # Enrichment
        self._project = project
        self._environment = environment
        self._version = version

        # Engine
        self._batch_size = batch_size
        self._poll_interval = poll_interval

    # ------------------------------------------------------------------

    def build(self) -> OkoEngine:
        """
        Собрать и запустить систему.

        Returns:
            Запущенный OkoEngine готовый принимать события.
        """
        connectors = self._build_connectors()
        output_handler = self._build_output_handler(connectors)

        pipeline = OkoPipeline(
            output_handler=output_handler,
            silence=self._silence,
            rate_limit_max=self._rate_limit_max,
            rate_limit_refill=self._rate_limit_refill,
            project=self._project,
            environment=self._environment,
            version=self._version,
        )

        engine = OkoEngine(
            handler=pipeline.process,
            batch_size=self._batch_size,
            poll_interval=self._poll_interval,
        )

        engine.start()
        logger.debug("OKO system built and started")
        return engine

    # ------------------------------------------------------------------
    # Сборка компонентов
    # ------------------------------------------------------------------

    def _build_connectors(self) -> List[BaseConnector]:
        """Собрать список активных коннекторов."""
        connectors: List[BaseConnector] = []

        # Telegram — если передан token и chat_id
        if self._telegram_token and self._telegram_chat_id:
            telegram = self._connector or TelegramConnector(
                token=self._telegram_token,
                chat_id=self._telegram_chat_id,
            )
            connectors.append(telegram)
        elif self._connector:
            # Кастомный коннектор без Telegram
            connectors.append(self._connector)

        # Дополнительные коннекторы (Webhook и т.д.)
        connectors.extend(self._extra_connectors)

        if not connectors:
            logger.warning(
                "OKO started without connectors — events will only be saved to storage"
            )

        return connectors

    def _build_output_handler(
        self,
        connectors: List[BaseConnector],
    ):
        """
        Собрать output_handler — функцию которую вызывает Pipeline.

        Она:
          1. Сохраняет пачку событий в Storage (всегда)
          2. Отправляет каждое событие в Connectors (async в отдельном потоке)
        """
        storage = self._storage

        def output_handler(events: List[OkoEvent]) -> None:
            # 1. Storage — синхронный batch insert
            storage.save_batch(events)

            # 2. Connectors — async отправка в отдельном потоке
            if connectors:
                _run_async_connectors(connectors, events)

        return output_handler


# ------------------------------------------------------------------
# Вспомогательная функция для запуска async коннекторов
# из синхронного Worker thread
# ------------------------------------------------------------------

def _run_async_connectors(
    connectors: List[BaseConnector],
    events: List[OkoEvent],
) -> None:
    """
    Запустить async коннекторы из синхронного потока.

    Worker работает в threading.Thread (синхронный контекст).
    Коннекторы (Telegram, Webhook) — async.

    Решение: создаём новый event loop в отдельном потоке.
    Не используем asyncio.run() напрямую — он создаёт loop
    только если нет текущего, но в Worker thread loop'а нет.
    """
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_send_all(connectors, events))
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=15.0)  # не ждём бесконечно


async def _send_all(
    connectors: List[BaseConnector],
    events: List[OkoEvent],
) -> None:
    """Отправить все события через все коннекторы."""
    for connector in connectors:
        for event in events:
            try:
                await connector.send(event)
            except Exception as exc:
                logger.exception(
                    "Connector %s failed: %s", connector, exc
                )