from __future__ import annotations

import traceback
import logging
from typing import Callable, List, Optional

from .event import OkoEvent
from .queue import OkoQueue
from .worker import OkoWorker

logger = logging.getLogger("oko.engine")


class OkoEngine:
    """
    Оркестратор Core layer — публичное API ядра системы.

    Именно через Engine все остальные слои взаимодействуют с Core:
        - Adapter вызывает engine.capture_*()
        - api/builder.py создаёт и конфигурирует Engine
        - Worker и Queue скрыты внутри

    Правило: Engine не знает про Telegram, SQLite, FastAPI.
    Он только принимает события и передаёт их в Pipeline через Worker.

    Жизненный цикл:
        engine = OkoEngine(handler=pipeline.process)
        engine.start()
        ...
        engine.capture_exception(exc)
        engine.capture_http_error(500, "POST", "/api/problems")
        ...
        engine.stop()
    """

    def __init__(
        self,
        handler: Callable[[List[OkoEvent]], None],
        queue_maxsize: int = 0,
        batch_size: int = 10,
        poll_interval: float = 1.0,
    ) -> None:
        """
        Args:
            handler:       функция обработки пачки событий (Pipeline)
            queue_maxsize: лимит очереди, 0 = безлимитный
            batch_size:    максимум событий за одну итерацию Worker
            poll_interval: секунд ждать если очередь пуста
        """
        self._queue = OkoQueue(maxsize=queue_maxsize)
        self._worker = OkoWorker(
            queue=self._queue,
            handler=handler,
            batch_size=batch_size,
            poll_interval=poll_interval,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запустить Engine. Вызывается из oko.init()."""
        self._worker.start()
        logger.debug("OkoEngine started")

    def stop(self, timeout: float = 5.0) -> None:
        """Graceful shutdown. Дообрабатывает события в очереди."""
        self._worker.stop(timeout=timeout)
        logger.debug("OkoEngine stopped")

    @property
    def is_running(self) -> bool:
        return self._worker.is_running

    # ------------------------------------------------------------------
    # Capture API — публичный интерфейс для Adapter layer
    # ------------------------------------------------------------------

    def capture_exception(
        self,
        exc: BaseException,
        context: Optional[dict] = None,
    ) -> None:
        """
        Перехватить исключение.

        Adapter вызывает это когда поймал необработанное исключение.

        Args:
            exc:     экземпляр исключения
            context: доп. контекст (метод, путь, заголовки и т.д.)
        """
        event = OkoEvent(
            type="error",
            message=f"{type(exc).__name__}: {exc}",
            stack=traceback.format_exc(),
            context=context or {},
        )
        self._enqueue(event)

    def capture_http_error(
        self,
        status_code: int,
        method: str,
        path: str,
        context: Optional[dict] = None,
    ) -> None:
        """
        Перехватить HTTP ошибку (4xx / 5xx).

        ASGI/WSGI middleware вызывает это после получения ответа.

        Args:
            status_code: HTTP статус (500, 404, ...)
            method:      HTTP метод ("GET", "POST", ...)
            path:        путь запроса ("/api/problems")
            context:     доп. контекст (заголовки, client_ip и т.д.)
        """
        ctx = {
            "status_code": status_code,
            "method": method,
            "path": path,
            **(context or {}),
        }
        event = OkoEvent(
            type="http_error",
            message=f"HTTP {status_code} {method} {path}",
            context=ctx,
        )
        self._enqueue(event)

    def capture_log(
        self,
        message: str,
        level: str = "info",
        context: Optional[dict] = None,
    ) -> None:
        """
        Захватить лог-сообщение вручную.

        Используется напрямую разработчиком или через logging handler.

        Example:
            core = oko.get_core()
            core.capture_log("Payment failed", level="warning")
        """
        event = OkoEvent(
            type="log",
            message=message,
            context={"level": level, **(context or {})},
        )
        self._enqueue(event)

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _enqueue(self, event: OkoEvent) -> None:
        """
        Положить событие в очередь.

        Единственная точка входа в очередь — чтобы
        в будущем легко добавить pre-enqueue фильтры.
        """
        self._queue.put(event)
        logger.debug("Enqueued: %s", event)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        status = "running" if self.is_running else "stopped"
        return f"OkoEngine(status={status}, queue_size={self._queue.size})"