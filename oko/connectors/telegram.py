from __future__ import annotations

import logging
from datetime import datetime

import httpx

from oko.connectors.base import BaseConnector
from oko.core.event import OkoEvent

logger = logging.getLogger("oko.connectors.telegram")

# Telegram Bot API endpoint
_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramConnector(BaseConnector):
    """
    Отправляет уведомления об ошибках через Telegram Bot API.

    Использование:
        connector = TelegramConnector(
            token="123456:ABC-DEF...",
            chat_id="987654321",
        )

    Формат сообщения:
        👁 OKO Alert

        🔴 500 POST /api/problems
        💬 HTTP 500 POST /api/problems

        🕐 14:23:05
        🌍 production | citymap

        [stack trace если есть — первые 10 строк]
    """

    def __init__(
        self,
        token: str,
        chat_id: str,
        timeout: float = 10.0,
    ) -> None:
        """
        Args:
            token:   токен Telegram бота (от @BotFather)
            chat_id: ID чата/пользователя куда слать уведомления
            timeout: таймаут HTTP запроса в секундах
        """
        self._token = token
        self._chat_id = chat_id
        self._timeout = timeout
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
        # Заголовок с типом события
        header = f"👁 *OKO ALERT*"
        if event.context.get("environment"):
            header += f" — {event.context['environment'].upper()}"
        
        lines = [header, ""]

        # Основная информация: Статус и Путь
        icon = self._icon(event)
        status = event.context.get("status_code", "")
        method = event.context.get("method", "").upper()
        path = event.context.get("path", "")

        if status and path:
            lines.append(f"{icon} *{status}* | {method} `{path}`")
        else:
            lines.append(f"{icon} *{event.type.upper()}*")

        # Сообщение об ошибке (выделяем курсивом для читаемости)
        lines.append(f"💬 _{self._escape(event.message)}_")
        lines.append("")

        # Метаданные (Проект, Время) в одну строку для компактности
        dt = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S")
        project = event.context.get("project", "unknown-app")
        lines.append(f"📦 *Project:* `{project}`")
        lines.append(f"🕒 *Time:* {dt}")

        # Stack trace: оформляем в блок кода
        if event.stack:
            stack_lines = event.stack.strip().splitlines()
            # Берем последние 10 строк, так как там обычно самое важное
            preview = "\n".join(stack_lines[-10:])
            lines.append("")
            lines.append("Traceback (last 10 lines):")
            lines.append(f"```python\n{preview}\n```")

        return "\n".join(lines)

    def _icon(self, event: OkoEvent) -> str:
        """Иконка в зависимости от критичности."""
        if event.is_server_error:
            return "❌" # Более стандартно для критических ошибок 5xx
        if event.is_client_error:
            return "⚠️" # Для 4xx
        if event.type == "log":
            return "ℹ️" 
        return "🔔"

    def _escape(self, text: str) -> str:
        """Экранирование спецсимволов для Markdown."""
        if not text:
            return ""
        # В режиме Markdown V1 нужно экранировать эти символы вне блоков кода
        return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _send_message(self, text: str) -> None:
        """Отправить сообщение через Telegram Bot API."""
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

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        # Не логируем токен
        return f"TelegramConnector(chat_id={self._chat_id!r})"