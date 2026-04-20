from __future__ import annotations

import logging
from typing import Any, Callable, FrozenSet, Iterable, Optional, Set

logger = logging.getLogger("oko.adapters.wsgi")

DEFAULT_CAPTURE_STATUS: FrozenSet[int] = frozenset({
    500, 501, 502, 503, 504,
    400, 405,
})


class OkoWSGIMiddleware:
    """
    WSGI middleware для перехвата HTTP ошибок.

    Работает с любым WSGI фреймворком:
        Flask, Django, Bottle

    Подключение Flask:
        app.wsgi_app = oko.WSGIMiddleware(app.wsgi_app)

    Подключение Django (wsgi.py):
        application = oko.WSGIMiddleware(get_wsgi_application())

    engine берётся автоматически из oko.get_engine() если не передан явно.
    """

    def __init__(
        self,
        app: Any,
        engine: Any = None,
        capture_status: Optional[Set[int]] = None,
    ) -> None:
        self.app = app
        self._engine = engine
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

    def __call__(
        self,
        environ: dict,
        start_response: Callable,
    ) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD", "")
        path   = environ.get("PATH_INFO", "")
        status_code: Optional[int] = None

        def start_response_wrapper(
            status: str,
            headers: list,
            exc_info: Any = None,
        ) -> Callable:
            nonlocal status_code
            try:
                status_code = int(status.split(" ", 1)[0])
            except (ValueError, IndexError):
                status_code = 0
            return start_response(status, headers, exc_info)

        try:
            result = self.app(environ, start_response_wrapper)
            if status_code in self.capture_status:
                self._capture_http_error(status_code, method, path, environ)
            return result
        except Exception as exc:
            self._capture_exception(exc, method, path, environ)
            raise

    def _capture_http_error(
        self,
        status_code: int,
        method: str,
        path: str,
        environ: dict,
    ) -> None:
        context = self._build_context(environ, status_code, method, path)
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
        environ: dict,
    ) -> None:
        context = self._build_context(environ, 500, method, path)
        self.engine.capture_exception(exc, context=context)

    def _build_context(
        self,
        environ: dict,
        status_code: int,
        method: str,
        path: str,
    ) -> dict:
        context: dict = {
            "status_code": status_code,
            "method": method,
            "path": path,
        }
        query = environ.get("QUERY_STRING", "")
        if query:
            context["query"] = query
        client_ip = (
            environ.get("HTTP_X_FORWARDED_FOR")
            or environ.get("REMOTE_ADDR", "")
        )
        if client_ip:
            context["client_ip"] = client_ip.split(",")[0].strip()
        user_agent = environ.get("HTTP_USER_AGENT", "")
        if user_agent:
            context["user_agent"] = user_agent
        return context