from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from oko.dashboard.core.repository import DashboardRepository
from oko.dashboard.core.service import DashboardService
from oko.storage.base import BaseStorage

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def create_dashboard_router(
    storage: BaseStorage,
    prefix: str = "/oko",
) -> APIRouter:
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
    router = APIRouter(prefix=prefix, tags=["oko-dashboard"])

    repo    = DashboardRepository(storage)
    service = DashboardService(repo)
    env     = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    # ------------------------------------------------------------------

    @router.get("/", response_class=HTMLResponse)
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

    @router.get("/{event_id}", response_class=HTMLResponse)
    async def event_detail(event_id: int) -> HTMLResponse:
        """Детальный просмотр одного события."""
        event = service.get_event_detail(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        html = env.get_template("event.html").render(event=event)
        return HTMLResponse(html)

    return router