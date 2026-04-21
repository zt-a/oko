"""
Tests for DashboardService.
"""
import pytest

from oko.dashboard.core.repository import DashboardRepository
from oko.dashboard.core.service import DashboardService
from oko.core.event import OkoEvent
from oko.storage.sqlite import SQLiteStorage


class TestDashboardServiceCreation:
    """Test DashboardService creation."""

    def test_create_service(self, memory_storage):
        """Test creating a service."""
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        assert service._repo == repo


class TestDashboardServiceGetEventsPage:
    """Test get_events_page method."""

    def test_get_events_page_empty(self, memory_storage):
        """Test getting events page from empty storage."""
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(limit=10)
        
        assert page.total == 0
        assert page.events == []

    def test_get_events_page_with_data(self, memory_storage):
        """Test getting events page with data."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(3)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(limit=10)
        
        assert page.total == 3
        assert len(page.events) == 3

    def test_get_events_page_respects_limit(self, memory_storage):
        """Test that page respects limit."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(10)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(limit=5)
        
        assert len(page.events) == 5

    def test_get_events_page_respects_offset(self, memory_storage):
        """Test that page respects offset."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(limit=2, offset=2)
        
        assert len(page.events) == 2

    def test_get_events_page_with_invalid_type(self, memory_storage):
        """Test page with invalid type filter."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        # Invalid type should be ignored
        page = service.get_events_page(event_type="invalid_type")
        
        assert page.total == 2

    def test_get_events_page_with_valid_type(self, memory_storage):
        """Test page with valid type filter."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="error", message="error 2"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(event_type="error")
        
        assert page.total == 2
        assert len(page.events) == 2

    def test_get_events_page_caps_limit(self, memory_storage):
        """Test that limit is capped at MAX_LIMIT."""
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(10)
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(limit=1000)
        
        assert page.limit <= 200  # MAX_LIMIT

    def test_get_events_page_clamps_offset(self, memory_storage):
        """Test that negative offset is clamped to 0."""
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        page = service.get_events_page(offset=-10)
        
        assert page.offset == 0


class TestDashboardServiceGetEventDetail:
    """Test get_event_detail method."""

    def test_get_event_detail_exists(self, memory_storage):
        """Test getting existing event detail."""
        event = OkoEvent(type="error", message="test")
        ids = memory_storage.save_batch_returning_ids([event])
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        detail = service.get_event_detail(ids[0])
        
        assert detail is not None
        assert detail.type == "error"

    def test_get_event_detail_not_exists(self, memory_storage):
        """Test getting non-existing event detail."""
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        detail = service.get_event_detail(999)
        
        assert detail is None


class TestDashboardServiceGetStats:
    """Test _get_stats method."""

    def test_get_stats(self, memory_storage):
        """Test getting stats."""
        events = [
            OkoEvent(type="error", message="error"),
            OkoEvent(type="log", message="log"),
            OkoEvent(type="http_error", message="http_error"),
        ]
        memory_storage.save_batch(events)
        
        repo = DashboardRepository(memory_storage)
        service = DashboardService(repo)
        
        stats = service._get_stats()
        
        assert stats.total == 3
        assert stats.errors == 1
        assert stats.logs == 1
        assert stats.http_errors == 1
