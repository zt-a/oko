from __future__ import annotations

import logging
import threading
from typing import Callable, List

from .event import OkoEvent
from .queue import OkoQueue

logger = logging.getLogger("oko.worker")


class OkoWorker:
    """
    Background worker — сердце Processing System.

    Запускается как daemon thread: живёт пока живёт основной процесс,
    умирает вместе с ним без явного shutdown (но shutdown тоже есть).

    Поток работы:
        Queue → get_batch → pipeline(event) → storage + connectors

    Правило: Worker не знает про Telegram, SQLite, FastAPI.
    Он только читает очередь и вызывает handler который ему передали.
    """

    def __init__(
        self,
        queue: OkoQueue,
        handler: Callable[[List[OkoEvent]], None],
        batch_size: int = 10,
        poll_interval: float = 1.0,
    ) -> None:
        """
        Args:
            queue:         откуда читать события
            handler:       что делать с пачкой событий
                           (Pipeline → Storage + Connectors)
            batch_size:    максимум событий за одну итерацию
            poll_interval: секунд ждать если очередь пуста
        """
        self._queue = queue
        self._handler = handler
        self._batch_size = batch_size
        self._poll_interval = poll_interval

        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="oko-worker",
            daemon=True,  # умирает вместе с основным процессом
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запустить worker. Вызывается один раз из oko.init()."""
        if self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread.start()
        logger.debug("OkoWorker started")

    def stop(self, timeout: float = 5.0) -> None:
        """
        Graceful shutdown.

        Сигналим остановиться, ждём timeout секунд.
        Worker успеет дообработать что осталось в очереди.
        """
        self._stop_event.set()
        self._thread.join(timeout=timeout)
        logger.debug("OkoWorker stopped")

    @property
    def is_running(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # Основной цикл
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """
        Основной цикл worker'а.

        Крутится пока не выставлен _stop_event.
        При остановке делает финальный flush — обрабатывает
        всё что осталось в очереди перед выходом.
        """
        while not self._stop_event.is_set():
            self._process_batch()

        # Финальный flush при остановке
        self._flush()
        logger.debug("OkoWorker final flush done")

    def _process_batch(self) -> None:
        """
        Одна итерация: взять пачку из очереди → передать в handler.

        Если очередь пуста — get() заблокируется на poll_interval
        и вернёт None, тогда просто идём на следующий круг.
        """
        # Сначала пробуем взять один элемент (с ожиданием)
        first = self._queue.get(timeout=self._poll_interval)
        if first is None:
            return

        # Есть хотя бы один — добираем остаток пачки без ожидания
        batch = [first] + self._queue.get_batch(max_size=self._batch_size - 1)

        self._handle(batch)

    def _flush(self) -> None:
        """Обработать всё что осталось в очереди при остановке."""
        while not self._queue.is_empty:
            batch = self._queue.get_batch(max_size=self._batch_size)
            if not batch:
                break
            self._handle(batch)

    def _handle(self, batch: List[OkoEvent]) -> None:
        """
        Вызвать handler с защитой от исключений.

        Worker не должен падать из-за ошибки в handler'е —
        он просто логирует и продолжает работу.
        """
        try:
            self._handler(batch)
        except Exception as exc:
            # Никогда не роняем worker из-за ошибки в pipeline/connector
            logger.exception("OkoWorker handler error: %s", exc)

    def __repr__(self) -> str:
        status = "running" if self.is_running else "stopped"
        return f"OkoWorker(status={status}, batch_size={self._batch_size})"