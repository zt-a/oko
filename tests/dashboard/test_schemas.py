"""
Tests for Dashboard schemas.
"""
import pytest

from oko.dashboard.core.schemas import EventRow, StatsRow, EventListPage
from oko.core.event import OkoEvent


class TestEventRowCreation:
    """Test EventRow creation."""

    def test_create_event_row(self):
        """Test creating an EventRow."""
        row = EventRow(
            id=1,
            type="error",
            message="Test error",
            stack="Traceback",
            context={"path": "/api/test"},
            timestamp=1234567890.0,
            fingerprint="abc123",
        )
        
        assert row.id == 1
        assert row.type == "error"
        assert row.message == "Test error"


class TestEventRowFromDict:
    """Test EventRow.from_dict method."""

    def test_from_dict(self):
        """Test creating EventRow from dict."""
        d = {
            "id": 1,
            "type": "error",
            "message": "Test error",
            "stack": "Traceback",
            "context": {"path": "/api/test"},
            "timestamp": 1234567890.0,
            "fingerprint": "abc123",
        }
        
        row = EventRow.from_dict(d)
        
        assert row.id == 1
        assert row.type == "error"


class TestEventRowProperties:
    """Test EventRow properties."""

    def test_status_code_property(self):
        """Test status_code property."""
        row = EventRow(
            id=1,
            type="http_error",
            message="500",
            stack="",
            context={"status_code": 500},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.status_code == 500

    def test_method_property(self):
        """Test method property."""
        row = EventRow(
            id=1,
            type="http_error",
            message="Get",
            stack="",
            context={"method": "GET"},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.method == "GET"

    def test_path_property(self):
        """Test path property."""
        row = EventRow(
            id=1,
            type="http_error",
            message="",
            stack="",
            context={"path": "/api/test"},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.path == "/api/test"

    def test_project_property(self):
        """Test project property."""
        row = EventRow(
            id=1,
            type="error",
            message="",
            stack="",
            context={"project": "myproject"},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.project == "myproject"

    def test_environment_property(self):
        """Test environment property."""
        row = EventRow(
            id=1,
            type="error",
            message="",
            stack="",
            context={"environment": "production"},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.environment == "production"

    def test_has_stack_property(self):
        """Test has_stack property."""
        row = EventRow(
            id=1,
            type="error",
            message="",
            stack="Traceback",
            context={},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.has_stack is True

    def test_has_stack_false_for_empty(self):
        """Test has_stack is False for empty stack."""
        row = EventRow(
            id=1,
            type="error",
            message="",
            stack="",
            context={},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.has_stack is False


class TestEventRowTypeLabel:
    """Test type_label property."""

    def test_type_label_for_server_error(self):
        """Test type_label for server error."""
        row = EventRow(
            id=1,
            type="http_error",
            message="500",
            stack="",
            context={"status_code": 500},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.type_label == "error"

    def test_type_label_for_client_error(self):
        """Test type_label for client error."""
        row = EventRow(
            id=1,
            type="http_error",
            message="404",
            stack="",
            context={"status_code": 404},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.type_label == "warning"

    def test_type_label_for_error(self):
        """Test type_label for error type."""
        row = EventRow(
            id=1,
            type="error",
            message="Error",
            stack="",
            context={},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.type_label == "error"

    def test_type_label_for_log(self):
        """Test type_label for log type."""
        row = EventRow(
            id=1,
            type="log",
            message="Log",
            stack="",
            context={},
            timestamp=1234567890.0,
            fingerprint="",
        )
        
        assert row.type_label == "info"


class TestStatsRowCreation:
    """Test StatsRow creation."""

    def test_create_stats_row(self):
        """Test creating a StatsRow."""
        stats = StatsRow(
            total=10,
            by_type={"error": 5, "log": 5},
        )
        
        assert stats.total == 10
        assert stats.errors == 5
        assert stats.logs == 5


class TestStatsRowProperties:
    """Test StatsRow properties."""

    def test_errors_property(self):
        """Test errors property."""
        stats = StatsRow(total=10, by_type={"error": 5})
        
        assert stats.errors == 5

    def test_http_errors_property(self):
        """Test http_errors property."""
        stats = StatsRow(total=10, by_type={"http_error": 3})
        
        assert stats.http_errors == 3

    def test_logs_property(self):
        """Test logs property."""
        stats = StatsRow(total=10, by_type={"log": 2})
        
        assert stats.logs == 2


class TestEventListPageCreation:
    """Test EventListPage creation."""

    def test_create_page(self):
        """Test creating an EventListPage."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=0),
            total=0,
            limit=10,
            offset=0,
            filter_type=None,
        )
        
        assert page.total == 0
        assert page.limit == 10


class TestEventListPagePagination:
    """Test EventListPage pagination properties."""

    def test_has_next_true(self):
        """Test has_next when more pages exist."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=25),
            total=25,
            limit=10,
            offset=10,
            filter_type=None,
        )
        
        assert page.has_next is True

    def test_has_next_false(self):
        """Test has_next when no more pages."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=5),
            total=5,
            limit=10,
            offset=0,
            filter_type=None,
        )
        
        assert page.has_next is False

    def test_has_prev_true(self):
        """Test has_prev when not first page."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=20),
            total=20,
            limit=10,
            offset=10,
            filter_type=None,
        )
        
        assert page.has_prev is True

    def test_has_prev_false(self):
        """Test has_prev when first page."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=5),
            total=5,
            limit=10,
            offset=0,
            filter_type=None,
        )
        
        assert page.has_prev is False

    def test_next_offset(self):
        """Test next_offset calculation."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=20),
            total=20,
            limit=10,
            offset=10,
            filter_type=None,
        )
        
        assert page.next_offset == 20

    def test_prev_offset(self):
        """Test prev_offset calculation."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=20),
            total=20,
            limit=10,
            offset=10,
            filter_type=None,
        )
        
        assert page.prev_offset == 0

    def test_prev_offset_not_negative(self):
        """Test prev_offset doesn't go negative."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=5),
            total=5,
            limit=10,
            offset=5,
            filter_type=None,
        )
        
        assert page.prev_offset == 0

    def test_page_number(self):
        """Test page_number calculation."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=55),
            total=55,
            limit=10,
            offset=20,
            filter_type=None,
        )
        
        assert page.page_number == 3

    def test_total_pages(self):
        """Test total_pages calculation."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=55),
            total=55,
            limit=10,
            offset=0,
            filter_type=None,
        )
        
        assert page.total_pages == 6

    def test_total_pages_single_page(self):
        """Test total_pages for single page."""
        page = EventListPage(
            events=[],
            stats=StatsRow(total=5),
            total=5,
            limit=10,
            offset=0,
            filter_type=None,
        )
        
        assert page.total_pages == 1