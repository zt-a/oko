"""
Tests for DashboardRepository.
"""
import pytest

from oko.dashboard.core.repository import DashboardRepository
from oko.core.event import OkoEvent
from oko.storage.sqlite import SQLiteStorage


class TestDashboardRepositoryCreation:
    """Test DashboardRepository creation."""

    def test_create_repository(self, memory_storage):
        """Test creating a repository."""
        repo = DashboardRepository(memory_storage)
        
        assert repo._storage == memory_storage


class TestDashboardRepositoryGetEvents:
    """Test get_events method."""

    def test_get_events_empty(self, memory_storage):
        """Test getting events from empty storage."""
        repo = DashboardRepository(memory_storage)
        
        events = repo.get_events(limit=10)
        
        assert events == []

    def test_get_events_with_data(self, memory_storage):
        """Test getting events with data."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(3)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        fetched = repo.get_events(limit=10)
        
        assert len(fetched) == 3

    def test_get_events_with_limit(self, memory_storage):
        """Test get_events respects limit."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(10)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        fetched = repo.get_events(limit=5)
        
        assert len(fetched) == 5

    def test_get_events_with_offset(self, memory_storage):
        """Test get_events with offset."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        fetched = repo.get_events(limit=2, offset=2)
        
        assert len(fetched) == 2

    def test_get_events_with_type_filter(self, memory_storage):
        """Test get_events with type filter."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="error", message="error 2"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        errors = repo.get_events(event_type="error")
        
        assert len(errors) == 2


class TestDashboardRepositoryGetEvent:
    """Test get_event method."""

    def test_get_existing_event(self, memory_storage):
        """Test getting existing event."""
        event = OkoEvent(type="error", message="test")
        ids = memory_storage.save_batch_returning_ids([event])
        
        repo = DashboardRepository(memory_storage)
        
        fetched = repo.get_event(ids[0])
        
        assert fetched is not None
        assert fetched["type"] == "error"

    def test_get_non_existing_event(self, memory_storage):
        """Test getting non-existing event."""
        repo = DashboardRepository(memory_storage)
        
        fetched = repo.get_event(999)
        
        assert fetched is None


class TestDashboardRepositoryCountEvents:
    """Test count_events method."""

    def test_count_empty(self, memory_storage):
        """Test counting empty storage."""
        repo = DashboardRepository(memory_storage)
        
        count = repo.count_events()
        
        assert count == 0

    def test_count_all(self, memory_storage):
        """Test counting all events."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        count = repo.count_events()
        
        assert count == 5

    def test_count_by_type(self, memory_storage):
        """Test counting by type."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="error", message="error 2"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        error_count = repo.count_events(event_type="error")
        
        assert error_count == 2


class TestDashboardRepositoryGetStats:
    """Test get_stats method."""

    def test_get_stats(self, memory_storage):
        """Test getting stats."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="http_error", message="http_error"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        
        stats = repo.get_stats()
        
        assert stats["total"] == 3
        assert stats["error"] == 1
        assert stats["log"] == 1
        assert stats["http_error"] == 1