from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from oko.connectors.base import BaseConnector
from oko.core.event import OkoEvent

logger = logging.getLogger("oko.connectors.webhook")


class WebhookConnector(BaseConnector):
    """
    Отправляет события на произвольный HTTP endpoint как JSON.

    Использование:
        connector = WebhookConnector(url="https://hooks.slack.com/...")

    Payload который получит endpoint:
        {
            "type":        "http_error",
            "message":     "HTTP 500 POST /api/problems",
            "stack":       "Traceback...",
            "context":     {"status_code": 500, "path": "/api/problems"},
            "timestamp":   1713541200.0,
            "fingerprint": "abc123..."
        }

    Кастомные заголовки:
        WebhookConnector(
            url="https://example.com/hook",
            headers={"Authorization": "Bearer secret"}
        )
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        method: str = "POST",
    ) -> None:
        """
        Args:
            url:     куда слать POST запрос
            headers: дополнительные заголовки (Auth, X-Api-Key и т.д.)
            timeout: таймаут HTTP запроса в секундах
            method:  HTTP метод, default POST
        """
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        self._method = method.upper()

    # ------------------------------------------------------------------

    async def send(self, event: OkoEvent) -> None:
        """Отправить одно событие как JSON POST."""
        payload = self._build_payload(event)
        await self._send_request(payload)

    # ------------------------------------------------------------------
    # Сборка payload
    # ------------------------------------------------------------------

    def _build_payload(self, event: OkoEvent) -> Dict[str, Any]:
        """
        Сериализовать событие в dict для JSON payload.

        Используем event.to_dict() — единственный правильный
        способ сериализации OkoEvent.
        """
        return event.to_dict()

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    async def _send_request(self, payload: Dict[str, Any]) -> None:
        """Отправить JSON payload на webhook URL."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method=self._method,
                    url=self._url,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
                logger.debug(
                    "Webhook sent ok: %s %s → %s",
                    self._method, self._url, response.status_code
                )

        except httpx.TimeoutException:
            logger.warning(
                "Webhook timeout after %.1fs: %s", self._timeout, self._url
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Webhook HTTP error: %s — %s",
                e.response.status_code, self._url
            )
        except Exception as e:
            logger.exception("Webhook unexpected error: %s", e)

    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"WebhookConnector(url={self._url!r}, method={self._method})"