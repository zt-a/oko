from __future__ import annotations

import logging
from typing import Callable, List, Optional

from oko.core.event import OkoEvent
from oko.pipeline.deduplication import DeduplicationProcessor
from oko.pipeline.enrichment import EnrichmentProcessor
from oko.pipeline.rate_limit import RateLimitProcessor

logger = logging.getLogger("oko.pipeline.processor")


class OkoPipeline:
    """
    Оркестратор Pipeline layer.

    Принимает пачку событий от Worker, прогоняет каждое через цепочку
    процессоров и передаёт прошедшие в output (Storage + Connectors).

    Цепочка обработки одного события:
        1. enrichment  — добавить контекст (project, env, python, os)
        2. deduplication — отбросить если уже было недавно
        3. rate_limit  — отбросить если превышен лимит уведомлений

    Правило: Pipeline не делает I/O.
    Output (Storage, Connectors) передаётся как callable — Pipeline
    не знает про Telegram и SQLite, он просто вызывает output_handler.

    Поток:
        Worker → pipeline.process(batch) → output_handler(filtered_batch)
    """

    def __init__(
        self,
        output_handler: Callable[[List[OkoEvent]], None],
        silence: float = 900.0,
        rate_limit_max: float = 10.0,
        rate_limit_refill: float = 1.0,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
    ) -> None:
        """
        Args:
            output_handler:    куда отправлять прошедшие события
                               (Storage + Connectors, передаётся из builder)
            silence:           silence window для дедупликации (секунды)
            rate_limit_max:    burst capacity токенов
            rate_limit_refill: восстановление токенов в секунду
            project:           название проекта для enrichment
            environment:       окружение для enrichment
            version:           версия приложения для enrichment
        """
        self._output_handler = output_handler

        self._enrichment = EnrichmentProcessor(
            project=project,
            environment=environment,
            version=version,
        )
        self._deduplication = DeduplicationProcessor(silence=silence)
        self._rate_limit = RateLimitProcessor(
            max_tokens=rate_limit_max,
            refill_rate=rate_limit_refill,
        )

    # ------------------------------------------------------------------
    # Главный метод — вызывается Worker'ом
    # ------------------------------------------------------------------

    def process(self, batch: List[OkoEvent]) -> None:
        """
        Обработать пачку событий.

        Каждое событие проходит через цепочку процессоров.
        Прошедшие все фильтры передаются в output_handler.

        Вызывается из Worker в фоновом потоке.
        """
        passed: List[OkoEvent] = []

        for event in batch:
            processed = self._process_one(event)
            if processed is not None:
                passed.append(processed)

        if passed:
            logger.debug(
                "Pipeline passed %d/%d events to output",
                len(passed), len(batch)
            )
            self._output_handler(passed)

    # ------------------------------------------------------------------
    # Внутренняя цепочка
    # ------------------------------------------------------------------

    def _process_one(self, event: OkoEvent) -> Optional[OkoEvent]:
        """
        Прогнать одно событие через все процессоры.

        Returns:
            OkoEvent если прошло все фильтры
            None    если было отброшено на каком-либо этапе
        """
        # Шаг 1: обогащение — всегда, для всех событий
        event = self._enrichment.enrich(event)

        # Шаг 2: дедупликация — отбросить дубликаты
        if not self._deduplication.should_send(event):
            logger.debug("Dropped by deduplication: %s", event)
            return None

        # Шаг 3: rate limiting — отбросить если превышен лимит
        if not self._rate_limit.should_send(event):
            logger.debug("Dropped by rate_limit: %s", event)
            return None

        return event

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"OkoPipeline("
            f"silence={self._deduplication.silence}s, "
            f"rate_limit={self._rate_limit.max_tokens}tokens)"
        )