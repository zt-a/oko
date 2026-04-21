from __future__ import annotations

import time
import logging

from oko.core.event import OkoEvent

logger = logging.getLogger("oko.pipeline.rate_limit")


class RateLimitProcessor:
    """
    Ограничивает количество уведомлений за период времени.

    Алгоритм: Token Bucket (ведро токенов).

        - Ведро вмещает max_tokens токенов.
        - Каждое событие тратит 1 токен.
        - Токены восстанавливаются со скоростью refill_rate/сек.
        - Если токенов нет — событие отбрасывается.

    Зачем Token Bucket а не просто счётчик:
        Счётчик "10 в минуту" позволяет сделать 10 запросов
        в последнюю секунду периода и 10 в первую секунду следующего —
        итого 20 подряд. Token Bucket это исключает.

    Пример (max_tokens=5, refill_rate=1/сек):
        10 событий подряд → первые 5 пройдут, остальные отброшены.
        Через 3 секунды → восстановится 3 токена, снова можно слать.

    Никакого I/O. Правило Pipeline: no I/O.
    """

    def __init__(
        self,
        max_tokens: float = 10.0,
        refill_rate: float = 1.0,
    ) -> None:
        """
        Args:
            max_tokens:  максимум токенов (burst capacity).
                         Сколько событий можно отправить подряд.
                         Default: 10.
            refill_rate: токенов в секунду для восстановления.
                         Default: 1.0 (1 токен каждую секунду).
        """
        self._max_tokens = max_tokens
        self._refill_rate = refill_rate
        self._tokens = max_tokens
        self._last_refill = time.time()

    # ------------------------------------------------------------------

    def should_send(self, event: OkoEvent) -> bool:
        """
        Решить — отправлять событие или нет.

        Returns:
            True  → токен есть → отправить
            False → токены кончились → отбросить
        """
        self._refill()

        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True

        logger.debug(
            "Rate limited %s — tokens=%.2f", event, self._tokens
        )
        return False

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _refill(self) -> None:
        """Восстановить токены пропорционально прошедшему времени."""
        now = time.time()
        elapsed = now - self._last_refill
        self._last_refill = now

        self._tokens = min(
            self._max_tokens,
            self._tokens + elapsed * self._refill_rate,
        )

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    @property
    def tokens(self) -> float:
        """Текущее количество токенов (приблизительно)."""
        return self._tokens

    @property
    def max_tokens(self) -> float:
        return self._max_tokens

    def __repr__(self) -> str:
        return (
            f"RateLimitProcessor("
            f"tokens={self._tokens:.1f}/{self._max_tokens}, "
            f"refill={self._refill_rate}/s)"
        )