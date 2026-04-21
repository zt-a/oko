from __future__ import annotations

import json
import logging
import sqlite3
import threading
from typing import Any, Dict, List, Optional

from oko.storage.base import BaseStorage

logger = logging.getLogger("oko.storage.sqlite")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS oko_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL,
    message     TEXT    NOT NULL,
    stack       TEXT    NOT NULL DEFAULT '',
    context     TEXT    NOT NULL DEFAULT '{}',
    timestamp   REAL    NOT NULL,
    fingerprint TEXT    NOT NULL
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_oko_type      ON oko_events(type);",
    "CREATE INDEX IF NOT EXISTS idx_oko_timestamp ON oko_events(timestamp DESC);",
    "CREATE INDEX IF NOT EXISTS idx_oko_fp        ON oko_events(fingerprint);",
]

_INSERT = """
INSERT INTO oko_events (type, message, stack, context, timestamp, fingerprint)
VALUES (?, ?, ?, ?, ?, ?)
"""

_FETCH = """
SELECT id, type, message, stack, context, timestamp, fingerprint
FROM oko_events
{where}
ORDER BY timestamp DESC
LIMIT ? OFFSET ?
"""

_COUNT = "SELECT COUNT(*) FROM oko_events {where}"


_CLEANUP = "DELETE FROM oko_events WHERE timestamp < ?"

class SQLiteStorage(BaseStorage):
    """
    Хранилище событий на базе SQLite.

    Особенности:
        - WAL mode: параллельные чтения не блокируют запись
        - batch insert: один executemany вместо N execute
        - thread lock: Worker и Dashboard могут работать одновременно
        - context сериализуется как JSON строка

    По умолчанию файл: oko.db в текущей директории.

    Использование:
        storage = SQLiteStorage()           # oko.db
        storage = SQLiteStorage("my.db")    # кастомный путь
        storage = SQLiteStorage(":memory:") # in-memory для тестов
    """

    def __init__(self, db_path: str = "oko.db", cleanup_days: int = 30) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._cleanup_days = cleanup_days
        # in-memory БД нельзя переоткрывать — держим одно соединение
        self._persistent_conn: Optional[sqlite3.Connection] = None
        if db_path == ":memory:":
            self._persistent_conn = self._open_conn()
        self._init_db()
        

    # ------------------------------------------------------------------
    # Соединение
    # ------------------------------------------------------------------

    def _open_conn(self) -> sqlite3.Connection:
        """Открыть новое соединение с WAL mode."""
        conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _connect(self) -> sqlite3.Connection:
        """Вернуть соединение: постоянное (memory) или новое (file)."""
        if self._persistent_conn is not None:
            return self._persistent_conn
        return self._open_conn()

    # ------------------------------------------------------------------
    # Инициализация
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        """Создать таблицу и индексы если не существуют."""
        conn = self._connect()
        conn.execute(_CREATE_TABLE)
        for idx in _CREATE_INDEXES:
            conn.execute(idx)
        conn.commit()
        # Вызываем очистку сразу после инициализации
        try:
            self.cleanup(days=self._cleanup_days)
        except Exception as e:
            logger.error("Failed to cleanup old events: %s", e)

        logger.debug("SQLiteStorage initialized: %s", self._db_path)

    # ------------------------------------------------------------------
    # Write (Processing System)
    # ------------------------------------------------------------------

    def save_batch(self, events: List[Any]) -> None:
        """
        Сохранить пачку событий одним batch insert.

        Вызывается из output_handler в Worker thread.
        Lock защищает от одновременной записи.
        """
        if not events:
            return

        rows = [
            (
                e.type,
                e.message,
                e.stack,
                json.dumps(e.context, ensure_ascii=False),
                e.timestamp,
                e.fingerprint,
            )
            for e in events
        ]

        with self._lock:
            conn = self._connect()
            conn.executemany(_INSERT, rows)
            conn.commit()

        logger.debug("SQLiteStorage saved batch of %d events", len(rows))

        # Раз в 100 сохранений запускаем чистку
        import random
        if random.random() < 0.01:
            try:
                self.cleanup(days=self._cleanup_days)
            except Exception as e:
                logger.error("Failed to cleanup old events: %s", e)

    def save_batch_returning_ids(self, events: List[Any]) -> List[int]:
        """
        Сохранить пачку событий и вернуть их id из БД.

        Используется в output_handler чтобы обогатить события
        database id перед отправкой в Connectors (для ссылок на dashboard).
        """
        if not events:
            return []

        rows = [
            (
                e.type,
                e.message,
                e.stack,
                json.dumps(e.context, ensure_ascii=False),
                e.timestamp,
                e.fingerprint,
            )
            for e in events
        ]

        with self._lock:
            conn = self._connect()
            cursor = conn.cursor()
            # Вставляем по одному чтобы получить lastrowid каждого
            ids = []
            for row in rows:
                cursor.execute(_INSERT, row)
                ids.append(cursor.lastrowid)
            conn.commit()

        logger.debug("SQLiteStorage saved batch of %d events, ids=%s", len(rows), ids)
        return ids

    # ------------------------------------------------------------------
    # Read (Observation System → Dashboard)
    # ------------------------------------------------------------------

    def fetch(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Получить события для Dashboard.

        Возвращает list[dict] — Dashboard не должен знать про OkoEvent.
        context десериализуется из JSON обратно в dict.
        """
        where, params = self._where_clause(event_type)
        query = _FETCH.format(where=where)
        conn = self._connect()
        rows = conn.execute(query, (*params, limit, offset)).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def count(self, event_type: Optional[str] = None) -> int:
        """Количество событий — для пагинации и статистики Dashboard."""
        where, params = self._where_clause(event_type)
        query = _COUNT.format(where=where)
        conn = self._connect()
        result = conn.execute(query, params).fetchone()
        return result[0] if result else 0

    def fetch_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получить одно событие по ID — для детального просмотра."""
        query = _FETCH.format(where="WHERE id = ?")
        conn = self._connect()
        row = conn.execute(query, (event_id, 1, 0)).fetchone()
        return self._row_to_dict(row) if row else None


    # ------------------------------------------------------------------
    # Очистка
    # ------------------------------------------------------------------

    def cleanup(self, days: int = 30) -> int:
        """
        Удалить события старше N дней.
        Возвращает количество удаленных записей.
        """
        # Вычисляем порог времени (текущий timestamp - секунды за N дней)
        import time
        threshold = time.time() - (days * 86400)

        with self._lock:
            conn = self._connect()
            cursor = conn.execute(_CLEANUP, (threshold,))
            deleted_count = cursor.rowcount
            conn.commit()
            
        if deleted_count > 0:
            logger.info("SQLiteStorage cleanup: removed %d events older than %d days", deleted_count, days)
        
        return deleted_count



    # ------------------------------------------------------------------
    # Утилиты
    # ------------------------------------------------------------------

    def _where_clause(self, event_type: Optional[str]) -> tuple:
        if event_type:
            return "WHERE type = ?", (event_type,)
        return "", ()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        try:
            d["context"] = json.loads(d["context"])
        except (json.JSONDecodeError, KeyError):
            d["context"] = {}
        return d

    def __repr__(self) -> str:
        return f"SQLiteStorage(path={self._db_path!r})"