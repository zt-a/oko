from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OkoEvent:
    """
    Единственный контракт передачи данных между слоями OKO.

    Правило: никаких raw dict между слоями — только OkoEvent.

    Поток:
        Adapter → OkoEvent → Core → Pipeline → Storage / Connectors
    """

    type: str
    """
    Тип события.
    Стандартные значения: "error", "log", "http_error", "unhandled"
    """

    message: str
    """Краткое описание события — первая строка ошибки или лог-сообщение."""

    stack: str = ""
    """Stack trace. Пустая строка если событие не связано с исключением."""

    context: dict[str, Any] = field(default_factory=dict)
    """
    Произвольный контекст события.
    Adapter кладёт сюда: метод, путь, статус код, заголовки и т.д.

    Пример:
        {
            "method": "POST",
            "path": "/api/problems",
            "status_code": 500,
            "client_ip": "127.0.0.1",
        }
    """

    timestamp: float = field(default_factory=time.time)
    """Unix timestamp момента создания события."""

    # ------------------------------------------------------------------
    # Вычисляемые свойства
    # ------------------------------------------------------------------

    @property
    def fingerprint(self) -> str:
        """
        Уникальный отпечаток события для дедупликации.

        Fingerprint строится из: type + path + status_code.
        Одинаковые ошибки на одном эндпоинте дают одинаковый fingerprint —
        Pipeline использует это чтобы не слать одно и то же уведомление дважды.
        """
        path        = self.context.get("path", "")
        status_code = str(self.context.get("status_code", ""))
        raw = f"{self.type}:{path}:{status_code}"
        return hashlib.md5(raw.encode()).hexdigest()

    @property
    def is_http_error(self) -> bool:
        """True если событие — HTTP ошибка (4xx / 5xx)."""
        status_code = self.context.get("status_code")
        return isinstance(status_code, int) and status_code >= 400

    @property
    def is_server_error(self) -> bool:
        """True если событие — серверная ошибка (5xx)."""
        status_code = self.context.get("status_code")
        return isinstance(status_code, int) and status_code >= 500

    @property
    def is_client_error(self) -> bool:
        """True если событие — клиентская ошибка (4xx)."""
        status_code = self.context.get("status_code")
        return isinstance(status_code, int) and 400 <= status_code < 500

    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для Storage (SQLite) и Connectors (Telegram)."""
        return {
            "type":        self.type,
            "message":     self.message,
            "stack":       self.stack,
            "context":     self.context,
            "timestamp":   self.timestamp,
            "fingerprint": self.fingerprint,
        }

    def __repr__(self) -> str:
        status = self.context.get("status_code", "")
        path   = self.context.get("path", "")
        status_str = f" {status}" if status else ""
        path_str   = f" {path}"   if path   else ""
        return f"OkoEvent(type={self.type!r}{status_str}{path_str})"