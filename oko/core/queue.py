from __future__ import annotations

import queue
from typing import List

from .event import OkoEvent


class OkoQueue:
    """
    Обёртка над queue.Queue из stdlib.

    Зачем обёртка а не голый queue.Queue:
        - Core не зависит от деталей реализации
        - Легко заменить внутренности не трогая Core
        - Единственное место где знают про queue.Queue

    Потокобезопасна — queue.Queue потокобезопасен по умолчанию.
    """

    def __init__(self, maxsize: int = 0) -> None:
        """
        maxsize=0 означает неограниченный размер очереди.
        Для production можно поставить лимит чтобы не съесть память.
        """
        self._queue: queue.Queue[OkoEvent] = queue.Queue(maxsize=maxsize)

    # ------------------------------------------------------------------
    # Запись
    # ------------------------------------------------------------------

    def put(self, event: OkoEvent) -> None:
        """
        Положить событие в очередь.

        Неблокирующий — если очередь переполнена (maxsize > 0),
        событие молча отбрасывается вместо блокировки request thread.
        """
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            # Философия OKO: не блокировать приложение разработчика.
            # Лучше потерять событие чем подвесить запрос.
            pass

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get(self, timeout: float = 1.0) -> OkoEvent | None:
        """
        Достать одно событие.

        Блокируется на timeout секунд — worker использует это
        чтобы не крутиться в busy loop когда очередь пуста.
        Возвращает None если за timeout ничего не пришло.
        """
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_batch(self, max_size: int = 10) -> List[OkoEvent]:
        """
        Достать пачку событий за раз (неблокирующий).

        Worker вызывает это перед batch insert в SQLite —
        лучше один раз записать 10 событий чем 10 раз по одному.
        """
        batch: List[OkoEvent] = []
        while len(batch) < max_size:
            try:
                event = self._queue.get_nowait()
                batch.append(event)
            except queue.Empty:
                break
        return batch

    # ------------------------------------------------------------------
    # Сигналы
    # ------------------------------------------------------------------

    def task_done(self) -> None:
        """
        Сигнал что событие обработано.
        Нужен если где-то используется queue.join().
        """
        self._queue.task_done()

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Приблизительный размер очереди (не точный в многопоточной среде)."""
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        return self._queue.empty()

    def __repr__(self) -> str:
        return f"OkoQueue(size={self.size})"