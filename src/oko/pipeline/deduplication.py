from __future__ import annotations

import time
import logging
from typing import Dict

from oko.core.event import OkoEvent

logger = logging.getLogger("oko.pipeline.deduplication")


class DeduplicationProcessor:
    """
    Убирает дублирующиеся события в пределах silence window.

    Принцип:
        Если одна и та же ошибка (одинаковый fingerprint) уже была
        отправлена недавно — не отправляем снова до истечения silence.

        Первое событие → пропускаем дальше + запоминаем время.
        Повторное событие в пределах silence → отбрасываем.
        После истечения silence → снова пропускаем.

    Состояние хранится в памяти — dict{fingerprint: last_sent_ts}.
    Никакого I/O. Правило Pipeline: no I/O.

    Пример:
        500 /api/problems в 14:00:00 → отправить
        500 /api/problems в 14:00:05 → тишина (silence=900)
        500 /api/problems в 14:15:01 → отправить (silence истёк)
        500 /api/users    в 14:00:00 → отправить (другой fingerprint)
    """

    def __init__(self, silence: float = 900.0) -> None:
        """
        Args:
            silence: секунд молчания после первого уведомления.
                     Default: 900 (15 минут).
                     0 = дедупликация отключена.
        """
        self._silence = silence
        self._seen: Dict[str, float] = {}  # fingerprint → last_sent_ts

    # ------------------------------------------------------------------

    def should_send(self, event: OkoEvent) -> bool:
        """
        Решить — отправлять событие или нет.

        Returns:
            True  → событие новое или silence истёк → отправить
            False → дубликат в пределах silence → отбросить
        """
        if self._silence <= 0:
            return True

        fp = event.fingerprint
        now = time.time()
        last_sent = self._seen.get(fp)

        if last_sent is None or (now - last_sent) >= self._silence:
            self._seen[fp] = now
            return True

        remaining = self._silence - (now - last_sent)
        logger.debug(
            "Deduplicated %s — silence %.0fs remaining", event, remaining
        )
        return False

    def reset(self, event: OkoEvent) -> None:
        """Сбросить silence для конкретного события (для тестов)."""
        self._seen.pop(event.fingerprint, None)

    def reset_all(self) -> None:
        """Сбросить весь silence state (для тестов)."""
        self._seen.clear()

    @property
    def silence(self) -> float:
        return self._silence

    @property
    def state_size(self) -> int:
        """Сколько fingerprint'ов сейчас в памяти."""
        return len(self._seen)

    def __repr__(self) -> str:
        return (
            f"DeduplicationProcessor("
            f"silence={self._silence}s, tracked={self.state_size})"
        )