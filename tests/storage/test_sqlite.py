"""
Tests for SQLiteStorage.
"""
import pytest
import time
import tempfile
import os

from oko.core.event import OkoEvent
from oko.storage.sqlite import SQLiteStorage


class TestSQLiteStorageCreation:
    """Test SQLiteStorage creation."""

    def test_create_in_memory_storage(self):
        """Test creating in-memory storage."""
        storage = SQLiteStorage(":memory:")
        
        assert storage is not None

    def test_create_file_storage(self):
        """Test creating file-based storage."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        storage = SQLiteStorage(db_path)
        
        try:
            assert storage is not None
        finally:
            os.unlink(db_path)

    def test_create_default_storage(self):
        """Test creating storage with default path."""
        storage = SQLiteStorage("test_default.db")
        
        try:
            assert storage is not None
        finally:
            if os.path.exists("test_default.db"):
                os.unlink("test_default.db")


class TestSQLiteStorageSaveBatch:
    """Test save_batch method."""

    def test_save_empty_batch(self, memory_storage):
        """Test saving empty batch does nothing."""
        memory_storage.save_batch([])
        
        count = memory_storage.count()
        assert count == 0

    def test_save_single_event(self, memory_storage):
        """Test saving single event."""
        event = OkoEvent(
            type="error",
            message="Test error",
            stack="Traceback",
            context={"path": "/api/test"},
        )
        
        memory_storage.save_batch([event])
        
        count = memory_storage.count()
        assert count == 1

    def test_save_multiple_events(self, memory_storage):
        """Test saving multiple events."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        
        memory_storage.save_batch(events)
        
        count = memory_storage.count()
        assert count == 5

    def test_save_batch_with_context(self, memory_storage):
        """Test saving events with context."""
        event = OkoEvent(
            type="error",
            message="test",
            context={
                "path": "/api/test",
                "method": "POST",
                "user_id": 123,
            },
        )
        
        memory_storage.save_batch([event])
        
        events = memory_storage.fetch(limit=10)
        assert events[0]["context"]["user_id"] == 123


class TestSQLiteStorageSaveBatchReturningIds:
    """Test save_batch_returning_ids method."""

    def test_save_and_get_ids(self, memory_storage):
        """Test saving events and getting their IDs."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(3)
        ]
        
        ids = memory_storage.save_batch_returning_ids(events)
        
        assert len(ids) == 3
        assert ids[0] < ids[1] < ids[2]

    def test_ids_sequence(self, memory_storage):
        """Test IDs are sequential."""
        event1 = OkoEvent(type="error", message="msg1")
        event2 = OkoEvent(type="error", message="msg2")
        
        ids = memory_storage.save_batch_returning_ids([event1, event2])
        
        # IDs should be consecutive (rowid)
        assert ids[1] == ids[0] + 1


class TestSQLiteStorageFetch:
    """Test fetch method."""

    def test_fetch_empty(self, memory_storage):
        """Test fetching from empty storage."""
        events = memory_storage.fetch(limit=10)
        
        assert events == []

    def test_fetch_events(self, memory_storage):
        """Test fetching events."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(3)
        ]
        memory_storage.save_batch(events)
        
        fetched = memory_storage.fetch(limit=10)
        
        assert len(fetched) == 3

    def test_fetch_with_limit(self, memory_storage):
        """Test fetch respects limit."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(10)
        ]
        memory_storage.save_batch(events)
        
        fetched = memory_storage.fetch(limit=5)
        
        assert len(fetched) == 5

    def test_fetch_with_offset(self, memory_storage):
        """Test fetch with offset."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        memory_storage.save_batch(events)
        
        fetched = memory_storage.fetch(limit=2, offset=2)
        
        assert len(fetched) == 2

    def test_fetch_by_type(self, memory_storage):
        """Test fetching by event type."""
        events = [
            OkoEvent(type="error", message="error msg"),
            OkoEvent(type="log", message="log msg"),
            OkoEvent(type="error", message="error msg 2"),
        ]
        memory_storage.save_batch(events)
        
        errors = memory_storage.fetch(event_type="error")
        
        assert len(errors) == 2
        for e in errors:
            assert e["type"] == "error"


class TestSQLiteStorageCount:
    """Test count method."""

    def test_count_empty(self, memory_storage):
        """Test counting empty storage."""
        count = memory_storage.count()
        
        assert count == 0

    def test_count_all(self, memory_storage):
        """Test counting all events."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        memory_storage.save_batch(events)
        
        count = memory_storage.count()
        
        assert count == 5

    def test_count_by_type(self, memory_storage):
        """Test counting by type."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="error", message="error 2"),
        ]
        memory_storage.save_batch(events)
        
        error_count = memory_storage.count(event_type="error")
        
        assert error_count == 2


class TestSQLiteStorageFetchById:
    """Test fetch_by_id method."""

    def test_fetch_existing_event(self, memory_storage):
        """Test fetching existing event by ID."""
        event = OkoEvent(type="error", message="test")
        ids = memory_storage.save_batch_returning_ids([event])
        
        fetched = memory_storage.fetch_by_id(ids[0])
        
        assert fetched is not None
        assert fetched["type"] == "error"
        assert fetched["message"] == "test"

    def test_fetch_non_existing_event(self, memory_storage):
        """Test fetching non-existing event returns None."""
        fetched = memory_storage.fetch_by_id(999)
        
        assert fetched is None


class TestSQLiteStorageCleanup:
    """Test cleanup method."""

    def test_cleanup_removes_old_events(self, temp_db_storage):
        """Test cleanup removes old events."""
        # Save event with old timestamp
        event = OkoEvent(
            type="error",
            message="old",
            timestamp=time.time() - (40 * 86400),  # 40 days old
        )
        temp_db_storage.save_batch([event])
        
        # Save recent event
        event2 = OkoEvent(
            type="error",
            message="recent",
        )
        temp_db_storage.save_batch([event2])
        
        # Cleanup events older than 30 days
        deleted = temp_db_storage.cleanup(days=30)
        
        assert deleted == 1
        
        count = temp_db_storage.count()
        assert count == 1

    def test_cleanup_keeps_recent_events(self, temp_db_storage):
        """Test cleanup keeps recent events."""
        event = OkoEvent(type="error", message="recent")
        temp_db_storage.save_batch([event])
        
        deleted = temp_db_storage.cleanup(days=30)
        
        assert deleted == 0
        
        count = temp_db_storage.count()
        assert count == 1


class TestSQLiteStorageContextSerialization:
    """Test context JSON serialization."""

    def test_save_and_fetch_complex_context(self, memory_storage):
        """Test saving and fetching complex context."""
        event = OkoEvent(
            type="error",
            message="test",
            context={
                "nested": {"key": "value"},
                "list": [1, 2, 3],
                "number": 42,
            },
        )
        
        memory_storage.save_batch([event])
        
        fetched = memory_storage.fetch(limit=1)[0]
        
        assert fetched["context"]["nested"]["key"] == "value"
        assert fetched["context"]["list"] == [1, 2, 3]
        assert fetched["context"]["number"] == 42


class TestSQLiteStorageRepr:
    """Test storage string representation."""

    def test_repr(self, memory_storage):
        """Test repr includes db path."""
        r = repr(memory_storage)
        
        assert "SQLiteStorage" in r