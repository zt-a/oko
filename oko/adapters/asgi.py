from __future__ import annotations

import logging
from typing import Any, Callable, FrozenSet, Optional, Set

logger = logging.getLogger("oko.adapters.asgi")

DEFAULT_CAPTURE_STATUS: FrozenSet[int] = frozenset({
    500, 501, 502, 503, 504,
    400, 405,
})


class OkoASGIMiddleware:
    """
    Чистый ASGI middleware для перехвата HTTP ошибок.

    Работает с любым ASGI фреймворком:
        FastAPI, Starlette, Litestar, Sanic, AIOHTTP

    Подключение FastAPI/Starlette:
        app.add_middleware(oko.ASGIMiddleware)
        # engine берётся автоматически из oko.get_engine()

    Или явно:
        app.add_middleware(oko.ASGIMiddleware, engine=engine)

    Универсальный ASGI способ:
        app = oko.ASGIMiddleware(app)
    """

    def __init__(
        self,
        app: Any,
        engine: Any = None,
        capture_status: Optional[Set[int]] = None,
    ) -> None:
        self.app = app
        self._engine = engine  # None → резолвится лениво из oko.get_engine()
        self.capture_status = (
            frozenset(capture_status)
            if capture_status is not None
            else DEFAULT_CAPTURE_STATUS
        )

    @property
    def engine(self) -> Any:
        """Лениво резолвим engine на момент первого запроса."""
        if self._engine is not None:
            return self._engine
        import oko
        return oko.get_engine()

    async def __call__(
        self,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        await self._handle_http(scope, receive, send)

    async def _handle_http(
        self,
        scope: dict,
        receive: Callable,
        send: Callable,
    ) -> None:
        status_code: Optional[int] = None
        method = scope.get("method", "")
        path = scope.get("path", "")

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)
            if (
                message["type"] == "http.response.start"
                and status_code in self.capture_status
            ):
                self._capture_http_error(status_code, method, path, scope)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            self._capture_exception(exc, method, path, scope)
            raise

    def _capture_http_error(
        self,
        status_code: int,
        method: str,
        path: str,
        scope: dict,
    ) -> None:
        context = self._build_context(scope, status_code, method, path)
        self.engine.capture_http_error(
            status_code=status_code,
            method=method,
            path=path,
            context=context,
        )

    def _capture_exception(
        self,
        exc: Exception,
        method: str,
        path: str,
        scope: dict,
    ) -> None:
        context = self._build_context(scope, 500, method, path)
        self.engine.capture_exception(exc, context=context)

    def _build_context(
        self,
        scope: dict,
        status_code: int,
        method: str,
        path: str,
    ) -> dict:
        context: dict = {
            "status_code": status_code,
            "method": method,
            "path": path,
        }
        query = scope.get("query_string", b"")
        if query:
            context["query"] = query.decode("utf-8", errors="replace")
        client = scope.get("client")
        if client:
            context["client_ip"] = client[0]
        headers = dict(scope.get("headers", []))
        if b"user-agent" in headers:
            context["user_agent"] = headers[b"user-agent"].decode(
                "utf-8", errors="replace"
            )
        return context