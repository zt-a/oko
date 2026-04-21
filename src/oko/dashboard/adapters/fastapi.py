from __future__ import annotations

from pathlib import Path
from typing import Optional, Any

from jinja2 import Environment, PackageLoader

from oko.dashboard.core.repository import DashboardRepository
from oko.dashboard.core.service import DashboardService
from oko.storage.base import BaseStorage


def create_dashboard_router(
    storage: BaseStorage,
    prefix: str = "/oko",
) -> Any:
    """
    Создать FastAPI роутер для Dashboard.

    Подключение:
        from oko.dashboard.adapters.fastapi import create_dashboard_router
        import oko

        router = create_dashboard_router(storage=oko.get_storage())
        app.include_router(router)

    Или через oko.init():
        oko.init(...)
        router = oko.dashboard_router()
        app.include_router(router)

    Args:
        storage: хранилище событий
        prefix:  URL префикс (default: /oko)

    Эндпоинты:
        GET /oko/          — список событий
        GET /oko/{id}      — детальный просмотр
    """
    # ЛОКАЛЬНЫЙ ИМПОРТ: 
    # Python попытается найти fastapi только в тот момент, 
    # когда пользователь реально вызовет эту функцию.
    try:
        from fastapi import APIRouter, HTTPException
        from fastapi.responses import HTMLResponse
    except ImportError:
        raise ImportError(
            "FastAPI is not installed. To use the dashboard, "
            "install it with: pip install fastapi jinja2"
        )
    router = APIRouter(prefix=prefix, tags=["oko-dashboard"])

    repo    = DashboardRepository(storage)
    service = DashboardService(repo)
    env = Environment(
        loader=PackageLoader("oko.dashboard", "templates"),
        autoescape=True,
    )

    # ------------------------------------------------------------------

    @router.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def events_list(
        type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> HTMLResponse:
        """Список событий с фильтрами и статистикой."""
        page = service.get_events_page(
            limit=limit,
            offset=offset,
            event_type=type,
        )
        html = env.get_template("events.html").render(page=page)
        return HTMLResponse(html)

    @router.get("/{event_id}", response_class=HTMLResponse, include_in_schema=False)
    async def event_detail(event_id: int) -> HTMLResponse:
        """Детальный просмотр одного события."""
        event = service.get_event_detail(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        html = env.get_template("event.html").render(event=event)
        return HTMLResponse(html)

    return router