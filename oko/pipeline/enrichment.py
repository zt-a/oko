from __future__ import annotations

import logging
import platform
import sys
from typing import Any, Dict, Optional

from oko.core.event import OkoEvent

logger = logging.getLogger("oko.pipeline.enrichment")


class EnrichmentProcessor:
    """
    Обогащает события дополнительным контекстом.

    Добавляет к каждому событию:
        - системная информация (python version, os, hostname)
        - пользовательские теги (project name, environment, version)

    Правило Pipeline: no I/O.
    Всё что здесь собирается — берётся один раз при инициализации
    из stdlib (platform, sys) и из конфига пользователя.
    Никаких HTTP запросов, никаких обращений к диску.
    """

    def __init__(
        self,
        project: Optional[str] = None,
        environment: Optional[str] = None,
        version: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Args:
            project:     название проекта ("citymap", "rateme")
            environment: окружение ("development", "production")
            version:     версия приложения ("1.0.0")
            extra:       произвольные теги {"team": "backend"}
        """
        # Собираем один раз при инициализации — не на каждый event
        self._static_context: Dict[str, Any] = {
            "python": sys.version.split()[0],
            "os": platform.system().lower(),
        }

        if project:
            self._static_context["project"] = project
        if environment:
            self._static_context["environment"] = environment
        if version:
            self._static_context["version"] = version
        if extra:
            self._static_context.update(extra)

    # ------------------------------------------------------------------

    def enrich(self, event: OkoEvent) -> OkoEvent:
        """
        Обогатить событие статическим контекстом.

        Не перезаписывает существующие ключи в event.context —
        Adapter уже мог положить туда method, path, status_code.
        Enrichment только добавляет то чего ещё нет.

        Returns:
            Тот же объект event с обновлённым context.
            (мутируем in-place — создавать копию нет смысла,
            event уже вышел из очереди и принадлежит pipeline)
        """
        for key, value in self._static_context.items():
            if key not in event.context:
                event.context[key] = value

        return event

    # ------------------------------------------------------------------

    @property
    def static_context(self) -> Dict[str, Any]:
        """Что будет добавлено к каждому событию."""
        return dict(self._static_context)

    def __repr__(self) -> str:
        keys = list(self._static_context.keys())
        return f"EnrichmentProcessor(adds={keys})"