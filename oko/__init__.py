"""
OKO 👁️ — Simple, zero-config error tracking for Python.

Быстрый старт:
    import oko
    oko.init(telegram_token="...", telegram_chat_id="...")

    # FastAPI / Starlette
    app.add_middleware(oko.ASGIMiddleware)

    # Flask / Django
    app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)

Явный захват:
    oko.capture_exception(exc)
    oko.capture_log("Something went wrong", level="warning")

Полный контроль:
    from oko.connectors.telegram import TelegramConnector
    from oko.storage.sqlite import SQLiteStorage

    oko.init(
        telegram_token="...",
        telegram_chat_id="...",
        storage=SQLiteStorage("custom.db"),
        silence=1800,
        project="myapp",
        environment="production",
    )
"""

from __future__ import annotations

import logging
from typing import List, Optional

from oko.adapters.asgi import OkoASGIMiddleware as ASGIMiddleware
from oko.adapters.wsgi import OkoWSGIMiddleware as WSGIMiddleware
from oko.adapters.logging_handler import (
    OkoLoggingHandler,
    install_logging_handler,
    make_loguru_sink,
)
from oko.api.builder import OkoBuilder
from oko.connectors.base import BaseConnector
from oko.connectors.telegram import TelegramConnector
from oko.connectors.webhook import WebhookConnector
from oko.core.engine import OkoEngine
from oko.core.event import OkoEvent
from oko.storage.base import BaseStorage
from oko.storage.sqlite import SQLiteStorage

__version__ = "0.1.0"
__all__ = [
    "init",
    "get_engine",
    "capture_exception",
    "capture_log",
    "capture_http_error",
    "loguru_sink",
    "ASGIMiddleware",
    "WSGIMiddleware",
    "OkoLoggingHandler",
    "install_logging_handler",
    "OkoEvent",
    "BaseConnector",
    "BaseStorage",
    "TelegramConnector",
    "WebhookConnector",
    "SQLiteStorage",
]

logger = logging.getLogger("oko")

# Модульный singleton — контролируется только через init()
_engine: Optional[OkoEngine] = None
_storage: Optional[BaseStorage] = None


def init(
    telegram_token: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    storage: Optional[BaseStorage] = None,
    db_path: str = "oko.db",
    connector: Optional[BaseConnector] = None,
    extra_connectors: Optional[List[BaseConnector]] = None,
    silence: float = 900.0,
    rate_limit_max: float = 10.0,
    rate_limit_refill: float = 1.0,
    project: Optional[str] = None,
    environment: Optional[str] = None,
    version: Optional[str] = None,
    capture_logs: bool = False,
    log_level: int = logging.ERROR,
    batch_size: int = 10,
    poll_interval: float = 1.0,
) -> OkoEngine:
    """
    Инициализировать OKO и запустить систему мониторинга.

    Минимальный вызов:
        oko.init()

    С Telegram:
        oko.init(telegram_token="...", telegram_chat_id="...")

    Полный конфиг:
        oko.init(
            telegram_token="...",
            telegram_chat_id="...",
            silence=1800,
            project="myapp",
            environment="production",
            capture_logs=True,
        )

    Returns:
        OkoEngine — запущенный движок системы
    """
    global _engine, _storage

    if _engine is not None and _engine.is_running:
        logger.warning("OKO already initialized — call ignored")
        return _engine

    _engine = OkoBuilder(
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        storage=storage,
        db_path=db_path,
        connector=connector,
        extra_connectors=extra_connectors,
        silence=silence,
        rate_limit_max=rate_limit_max,
        rate_limit_refill=rate_limit_refill,
        project=project,
        environment=environment,
        version=version,
        batch_size=batch_size,
        poll_interval=poll_interval,
    ).build()


    # Сохраняем storage для Dashboard
    _storage = storage or SQLiteStorage(db_path)


    if capture_logs:
        install_logging_handler(_engine, level=log_level)

    logger.debug("OKO initialized ✓")
    return _engine


def get_engine() -> OkoEngine:
    """
    Получить текущий engine.

    Raises:
        RuntimeError: если oko.init() ещё не был вызван
    """
    if _engine is None:
        raise RuntimeError("OKO not initialized. Call oko.init() first.")
    return _engine


def capture_exception(
    exc: BaseException,
    context: Optional[dict] = None,
) -> None:
    """
    Захватить исключение вручную.

    Example:
        try:
            risky_operation()
        except Exception as e:
            oko.capture_exception(e)
    """
    get_engine().capture_exception(exc, context=context)


def capture_log(
    message: str,
    level: str = "info",
    context: Optional[dict] = None,
) -> None:
    """
    Захватить лог-сообщение вручную.

    Example:
        oko.capture_log("Payment failed", level="warning")
        oko.capture_log("User banned", context={"user_id": 42})
    """
    get_engine().capture_log(message, level=level, context=context)


def capture_http_error(
    status_code: int,
    method: str,
    path: str,
    context: Optional[dict] = None,
) -> None:
    """
    Захватить HTTP ошибку вручную.

    Example:
        oko.capture_http_error(500, "POST", "/api/problems")
    """
    get_engine().capture_http_error(
        status_code=status_code,
        method=method,
        path=path,
        context=context,
    )


def loguru_sink(level: str = "ERROR"):
    """
    Фабрика sink для Loguru.

    Example:
        from loguru import logger
        import oko

        logger.add(oko.loguru_sink(), level="ERROR")
    """
    return make_loguru_sink(engine=get_engine())



# ------------------------------------------------------------------
# Dashboard API
# ------------------------------------------------------------------
 
def get_storage() -> BaseStorage:
    """
    Получить текущий storage.
 
    Raises:
        RuntimeError: если oko.init() ещё не был вызван
    """
    if _storage is None:
        raise RuntimeError("OKO not initialized. Call oko.init() first.")
    return _storage
 
 
def dashboard_router(prefix: str = "/oko"):
    """
    Создать FastAPI роутер для Dashboard.
 
    Подключение:
        oko.init(...)
        app.include_router(oko.dashboard_router())
 
    Args:
        prefix: URL префикс (default: /oko)
    """
    from oko.dashboard.adapters.fastapi import create_dashboard_router
    return create_dashboard_router(storage=get_storage(), prefix=prefix)
 
