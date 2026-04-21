from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from oko.dashboard.core.repository import DashboardRepository
from oko.dashboard.core.service import DashboardService
from oko.storage.base import BaseStorage

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def create_dashboard_blueprint(
    storage: BaseStorage,
    url_prefix: str = "/oko",
) -> Any:
    """
    Создать Flask Blueprint для Dashboard.

    Подключение:
        from oko.dashboard.adapters.flask import create_dashboard_blueprint
        import oko

        app = Flask(__name__)
        app.register_blueprint(
            create_dashboard_blueprint(storage=oko.get_storage())
        )

    Или через oko.init():
        oko.init(...)
        app.register_blueprint(oko.dashboard_blueprint())

    Args:
        storage: хранилище событий
        url_prefix: URL префикс (default: /oko)

    Эндпоинты:
        GET /oko/          — список событий
        GET /oko/<id>      — детальный просмотр
    """
    try:
        from flask import Blueprint, render_template, abort
    except ImportError:
        raise ImportError(
            "Flask is not installed. To use the dashboard, "
            "install it with: pip install flask jinja2"
        )

    blueprint = Blueprint("oko_dashboard", __name__, url_prefix=url_prefix)

    repo = DashboardRepository(storage)
    service = DashboardService(repo)
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    # ------------------------------------------------------------------

    @blueprint.route("/")
    def events_list():
        """Список событий с фильтрами и статистикой."""
        from flask import request
        
        type_filter = request.args.get("type")
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        
        page = service.get_events_page(
            limit=limit,
            offset=offset,
            event_type=type_filter,
        )
        
        return render_template("events.html", page=page)

    @blueprint.route("/<int:event_id>")
    def event_detail(event_id: int):
        """Детальный просмотр одного события."""
        event = service.get_event_detail(event_id)
        
        if event is None:
            abort(404)
        
        return render_template("event.html", event=event)

    return blueprint
