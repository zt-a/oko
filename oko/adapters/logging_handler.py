from __future__ import annotations

import logging
import traceback
from typing import Any, Optional
from oko.adapters.base import BaseAdapter
from oko.adapters.logging_handler import install_logging_handler

logger = logging.getLogger("oko.adapters.logging")


class OkoLoggingHandler(logging.Handler):
    """
    Стандартный logging.Handler — вешается на Python logger.

    Два способа использования:

    1. Автоматически (через oko.init):
        oko.init(capture_logs=True)
        # OKO сам вешается на root logger и перехватывает ERROR+

    2. Вручную на конкретный logger:
        import logging
        import oko

        handler = OkoLoggingHandler(engine=oko.get_engine())
        logging.getLogger("myapp").addHandler(handler)

    Перехватывает уровни: ERROR, CRITICAL (по умолчанию).
    WARNING и ниже — игнорируются если не задать явно.
    """

    def __init__(
        self,
        engine: Any,
        level: int = logging.ERROR,
    ) -> None:
        """
        Args:
            engine: OkoEngine — куда передавать события
            level:  минимальный уровень логирования для перехвата
                    Default: ERROR (WARNING и INFO игнорируются)
        """
        super().__init__(level=level)
        self.engine = engine

    def emit(self, record: logging.LogRecord) -> None:
        """
        Вызывается logging системой при каждом подходящем лог-записи.

        Преобразуем LogRecord → OkoEvent через engine.capture_log().
        """
        try:
            message = self.format(record)

            # Если есть exc_info — захватываем как исключение
            if record.exc_info and record.exc_info[1] is not None:
                exc = record.exc_info[1]
                self.engine.capture_exception(
                    exc,
                    context={
                        "logger": record.name,
                        "level": record.levelname,
                        "module": record.module,
                        "funcName": record.funcName,
                        "lineno": record.lineno,
                    },
                )
            else:
                self.engine.capture_log(
                    message=record.getMessage(),
                    level=record.levelname.lower(),
                    context={
                        "logger": record.name,
                        "module": record.module,
                        "funcName": record.funcName,
                        "lineno": record.lineno,
                    },
                )

        except Exception:
            # Никогда не роняем приложение из-за ошибки в handler
            self.handleError(record)


def make_loguru_sink(engine: Any) -> Any:
    """
    Фабрика sink-функции для Loguru.

    Loguru sink — это callable который loguru вызывает при каждом логе.

    Использование:
        from loguru import logger
        import oko

        logger.add(oko.loguru_sink())  # через публичный API

        # или вручную:
        from oko.adapters.logging_handler import make_loguru_sink
        logger.add(make_loguru_sink(engine=oko.get_engine()), level="ERROR")
    """

    def loguru_sink(message: Any) -> None:
        """
        Loguru sink.

        message — объект loguru Message с атрибутом record (dict).
        """
        try:
            record = message.record

            level    = record["level"].name.lower()
            text     = record["message"]
            exc      = record.get("exception")
            mod      = record.get("module", "")
            func     = record.get("function", "")
            lineno   = record.get("line", 0)
            log_name = record.get("name", "")

            context = {
                "logger":   log_name,
                "module":   mod,
                "funcName": func,
                "lineno":   lineno,
            }

            if exc is not None:
                # exc это tuple (type, value, tb) как в sys.exc_info()
                exc_value = exc[1] if exc[1] is not None else None
                if exc_value:
                    engine.capture_exception(exc_value, context=context)
                    return

            engine.capture_log(
                message=text,
                level=level,
                context=context,
            )

        except Exception:
            # Не роняем приложение из-за ошибки в sink
            pass

    return loguru_sink


def install_logging_handler(
    engine: Any,
    level: int = logging.ERROR,
    logger_name: Optional[str] = None,
) -> OkoLoggingHandler:
    """
    Удобная функция — установить OkoLoggingHandler на logger.

    Args:
        engine:      OkoEngine
        level:       минимальный уровень (default: ERROR)
        logger_name: имя logger, None = root logger

    Returns:
        установленный handler (чтобы можно было снять если нужно)
    """
    target_logger = logging.getLogger(logger_name)
    handler = OkoLoggingHandler(engine=engine, level=level)
    target_logger.addHandler(handler)
    logger.debug(
        "OkoLoggingHandler installed on logger=%r level=%s",
        logger_name or "root", logging.getLevelName(level)
    )
    return handler

class LoggingAdapter(BaseAdapter):
    def __init__(self, engine: Any = None, level: int = logging.ERROR):
        super().__init__(engine)
        self.level = level

    def install(self, app: Any = None) -> None:
        # Здесь 'app' может быть именем логгера. По умолчанию — root.
        install_logging_handler(engine=self.engine, level=self.level, logger_name=app)