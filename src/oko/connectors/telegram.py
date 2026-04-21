from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import httpx

from oko.connectors.base import BaseConnector
from oko.core.event import OkoEvent

logger = logging.getLogger("oko.connectors.telegram")

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramConnector(BaseConnector):
    """
    Отправляет уведомления об ошибках через Telegram Bot API.

    Использование:
        connector = TelegramConnector(
            token="123456:ABC-DEF...",
            chat_id="987654321",
            dashboard_url="https://myapp.com",  # опционально
        )

    Формат сообщения:
        👁 OKO ALERT — PRODUCTION

        ❌ *500* | POST `/api/problems`
        💬 _HTTP 500 POST /api/problems_

        📦 *Project:* `citymap`
        🕒 *Time:* 14:23:05

        🔗 http://myapp.com/oko/42   ← ссылка на dashboard (если задан)

        Traceback (last 10 lines):
        ```python
        ...
        ```
    """

    def __init__(
        self,
        token: str,
        chat_id: str,
        timeout: float = 10.0,
        dashboard_url: Optional[str] = None,
    ) -> None:
        """
        Args:
            token:          токен Telegram бота (от @BotFather)
            chat_id:        ID чата/пользователя куда слать уведомления
            timeout:        таймаут HTTP запроса в секундах
            dashboard_url:  base URL приложения для ссылок на dashboard.
                            Например: "http://localhost:8000" или "https://myapp.com"
                            Если не задан — ссылки в сообщениях не будет.
        """
        self._token = token
        self._chat_id = chat_id
        self._timeout = timeout
        self._dashboard_url = dashboard_url.rstrip("/") if dashboard_url else None
        self._url = _TELEGRAM_API.format(token=token)

    # ------------------------------------------------------------------

    async def send(self, event: OkoEvent) -> None:
        """Отправить одно событие в Telegram."""
        text = self._format(event)
        await self._send_message(text)

    # ------------------------------------------------------------------
    # Форматирование
    # ------------------------------------------------------------------

    def _format(self, event: OkoEvent) -> str:
        """Сформировать красиво отформатированное сообщение для Telegram."""
        header = "👁 *OKO ALERT*"
        if event.context.get("environment"):
            header += f" — {event.context['environment'].upper()}"

        lines = [header, ""]

        icon = self._icon(event)
        status = event.context.get("status_code", "")
        method = event.context.get("method", "").upper()
        path = event.context.get("path", "")

        if status and path:
            lines.append(f"{icon} *{status}* | {method} `{path}`")
        else:
            lines.append(f"{icon} *{event.type.upper()}*")

        lines.append(f"💬 _{self._escape(event.message)}_")
        lines.append("")

        dt = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        project = event.context.get("project", "unknown-app")
        lines.append(f"📦 *Project:* `{project}`")
        lines.append(f"🕒 *Time:* {dt}")

        # Ссылка на dashboard event
        event_id = event.context.get("id")
        if self._dashboard_url and event_id is not None:
            # Заменяем 'localhost' на '127.0.0.1' для стабильности ссылок в Telegram
            base_url = self._dashboard_url.replace("localhost", "127.0.0.1")
            url = f"{base_url}/oko/{event_id}"
            
            # Используем явное оформление Markdown [Текст](URL)
            # Важно: саму переменную url НЕ пропускаем через self._escape, 
            # чтобы не сломать протокол http:// и точки
            lines.append(f"🔗 [{url}]({url})")

        # Stack trace
        if event.stack:
            stack_lines = event.stack.strip().splitlines()
            preview = "\n".join(stack_lines[-10:])
            lines.append("")
            lines.append("Traceback (last 10 lines):")
            lines.append(f"```python\n{preview}\n```")

        return "\n".join(lines)

    def _icon(self, event: OkoEvent) -> str:
        if event.is_server_error:
            return "❌"
        if event.is_client_error:
            return "⚠️"
        if event.type == "log":
            return "ℹ️"
        return "🔔"

    def _escape(self, text: str) -> str:
        if not text:
            return ""
        return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _send_message(self, text: str) -> None:
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=payload)
                response.raise_for_status()
                logger.debug("Telegram message sent ok")

        except httpx.TimeoutException:
            logger.warning("Telegram send timeout after %.1fs", self._timeout)
        except httpx.HTTPStatusError as e:
            logger.error(
                "Telegram API error: %s — %s",
                e.response.status_code,
                e.response.text,
            )
        except Exception as e:
            logger.exception("Telegram unexpected error: %s", e)

    def __repr__(self) -> str:
        return f"TelegramConnector(chat_id={self._chat_id!r}, dashboard_url={self._dashboard_url!r})"