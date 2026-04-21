"""
Tests for OkoEvent model.
"""
import time
import pytest
from oko.core.event import OkoEvent


class TestOkoEventCreation:
    """Test OkoEvent creation and basic properties."""

    def test_create_basic_event(self):
        """Test creating a basic event."""
        event = OkoEvent(
            type="error",
            message="Test error",
            stack="",
        )
        
        assert event.type == "error"
        assert event.message == "Test error"
        assert event.stack == ""
        assert event.timestamp > 0

    def test_create_event_with_context(self):
        """Test creating event with context."""
        context = {
            "path": "/api/test",
            "method": "POST",
            "status_code": 500,
        }
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context=context,
        )
        
        assert event.context["path"] == "/api/test"
        assert event.context["method"] == "POST"
        assert event.context["status_code"] == 500

    def test_create_event_with_timestamp(self):
        """Test creating event with custom timestamp."""
        custom_timestamp = 1234567890.0
        event = OkoEvent(
            type="error",
            message="Test",
            timestamp=custom_timestamp,
        )
        
        assert event.timestamp == custom_timestamp

    def test_default_timestamp_is_set(self):
        """Test that default timestamp is set on creation."""
        before = time.time()
        event = OkoEvent(type="error", message="Test")
        after = time.time()
        
        assert before <= event.timestamp <= after


class TestOkoEventFingerprint:
    """Test fingerprint calculation."""

    def test_fingerprint_for_http_error(self):
        """Test fingerprint for HTTP error events."""
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        fp = event.fingerprint
        assert isinstance(fp, str)
        assert len(fp) == 32  # MD5 hash length

    def test_same_events_same_fingerprint(self):
        """Test that identical events have the same fingerprint."""
        event1 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        event2 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        assert event1.fingerprint == event2.fingerprint

    def test_different_events_different_fingerprint(self):
        """Test that different events have different fingerprints."""
        event1 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test1", "status_code": 500},
        )
        event2 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test2", "status_code": 500},
        )
        
        assert event1.fingerprint != event2.fingerprint


class TestOkoEventStatusChecks:
    """Test HTTP status check properties."""

    def test_is_http_error_true_for_400(self):
        """Test is_http_error returns True for 400."""
        event = OkoEvent(
            type="http_error",
            message="Bad Request",
            context={"status_code": 400},
        )
        assert event.is_http_error is True

    def test_is_http_error_true_for_500(self):
        """Test is_http_error returns True for 500."""
        event = OkoEvent(
            type="http_error",
            message="Server Error",
            context={"status_code": 500},
        )
        assert event.is_http_error is True

    def test_is_http_error_false_for_200(self):
        """Test is_http_error returns False for 200."""
        event = OkoEvent(
            type="log",
            message="OK",
            context={"status_code": 200},
        )
        assert event.is_http_error is False

    def test_is_http_error_false_without_status(self):
        """Test is_http_error returns False without status_code."""
        event = OkoEvent(
            type="error",
            message="Error",
            context={},
        )
        assert event.is_http_error is False

    def test_is_server_error_true_for_500(self):
        """Test is_server_error returns True for 500."""
        event = OkoEvent(
            type="http_error",
            message="Server Error",
            context={"status_code": 500},
        )
        assert event.is_server_error is True

    def test_is_server_error_false_for_400(self):
        """Test is_server_error returns False for 400."""
        event = OkoEvent(
            type="http_error",
            message="Bad Request",
            context={"status_code": 400},
        )
        assert event.is_server_error is False

    def test_is_client_error_true_for_400(self):
        """Test is_client_error returns True for 400."""
        event = OkoEvent(
            type="http_error",
            message="Bad Request",
            context={"status_code": 400},
        )
        assert event.is_client_error is True

    def test_is_client_error_true_for_404(self):
        """Test is_client_error returns True for 404."""
        event = OkoEvent(
            type="http_error",
            message="Not Found",
            context={"status_code": 404},
        )
        assert event.is_client_error is True

    def test_is_client_error_false_for_500(self):
        """Test is_client_error returns False for 500."""
        event = OkoEvent(
            type="http_error",
            message="Server Error",
            context={"status_code": 500},
        )
        assert event.is_client_error is False


class TestOkoEventSerialization:
    """Test event serialization."""

    def test_to_dict(self):
        """Test event serialization to dict."""
        event = OkoEvent(
            type="error",
            message="Test error",
            stack="Traceback",
            context={"path": "/api/test"},
        )
        
        d = event.to_dict()
        
        assert isinstance(d, dict)
        assert d["type"] == "error"
        assert d["message"] == "Test error"
        assert d["stack"] == "Traceback"
        assert d["context"]["path"] == "/api/test"
        assert "timestamp" in d
        assert "fingerprint" in d

    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all fields."""
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            stack="",
            context={"method": "POST", "path": "/api/test"},
        )
        
        d = event.to_dict()
        
        expected_keys = {"type", "message", "stack", "context", "timestamp", "fingerprint"}
        assert expected_keys == set(d.keys())


class TestOkoEventRepr:
    """Test event string representation."""

    def test_repr_basic(self):
        """Test basic repr."""
        event = OkoEvent(
            type="error",
            message="Test",
        )
        r = repr(event)
        assert "error" in r

    def test_repr_with_status(self):
        """Test repr with status code."""
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"status_code": 500, "path": "/api/test"},
        )
        r = repr(event)
        
        assert "500" in r
        assert "/api/test" in r
