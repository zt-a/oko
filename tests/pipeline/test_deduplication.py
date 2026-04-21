"""
Tests for DeduplicationProcessor.
"""
import pytest
import time

from oko.core.event import OkoEvent
from oko.pipeline.deduplication import DeduplicationProcessor


class TestDeduplicationProcessorCreation:
    """Test DeduplicationProcessor creation."""

    def test_create_processor_default_silence(self):
        """Test creating processor with default silence."""
        processor = DeduplicationProcessor()
        
        assert processor.silence == 900.0

    def test_create_processor_custom_silence(self):
        """Test creating processor with custom silence."""
        processor = DeduplicationProcessor(silence=60.0)
        
        assert processor.silence == 60.0

    def test_zero_silence_disables_dedup(self):
        """Test that zero silence disables deduplication."""
        processor = DeduplicationProcessor(silence=0.0)
        
        event = OkoEvent(type="error", message="test")
        
        assert processor.should_send(event) is True
        assert processor.should_send(event) is True


class TestDeduplicationProcessorShouldSend:
    """Test should_send method."""

    def test_first_event_passes(self):
        """Test that first event always passes."""
        processor = DeduplicationProcessor(silence=60.0)
        
        event = OkoEvent(type="error", message="test")
        
        assert processor.should_send(event) is True

    def test_duplicate_blocked_in_silence(self):
        """Test that duplicate is blocked within silence window."""
        processor = DeduplicationProcessor(silence=60.0)
        
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        processor.should_send(event)  # First passes
        
        result = processor.should_send(event)  # Second should be blocked
        
        assert result is False

    def test_different_fingerprints_pass(self):
        """Test that different fingerprints pass."""
        processor = DeduplicationProcessor(silence=60.0)
        
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
        
        assert processor.should_send(event1) is True
        assert processor.should_send(event2) is True  # Different fingerprint

    def test_after_silence_expires(self):
        """Test that events pass after silence expires."""
        processor = DeduplicationProcessor(silence=0.1)  # Short silence
        
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        processor.should_send(event)  # First
        
        time.sleep(0.15)  # Wait for silence to expire
        
        result = processor.should_send(event)  # Should pass now
        
        assert result is True


class TestDeduplicationProcessorReset:
    """Test reset methods."""

    def test_reset_single_event(self):
        """Test resetting single event."""
        processor = DeduplicationProcessor(silence=60.0)
        
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        processor.should_send(event)
        assert processor.should_send(event) is False  # Blocked
        
        processor.reset(event)
        
        assert processor.should_send(event) is True  # Now passes

    def test_reset_all(self):
        """Test resetting all events."""
        processor = DeduplicationProcessor(silence=60.0)
        
        events = [
            OkoEvent(
                type="http_error",
                message=f"HTTP {code}",
                context={"path": f"/api/test{i}", "status_code": code},
            )
            for i, code in enumerate([500, 404, 400])
        ]
        
        for e in events:
            processor.should_send(e)
        
        # All should be blocked now
        for e in events:
            processor.should_send(e)
        
        processor.reset_all()
        
        # All should pass now
        for e in events:
            assert processor.should_send(e) is True


class TestDeduplicationProcessorState:
    """Test state tracking."""

    def test_state_size(self):
        """Test state size property."""
        processor = DeduplicationProcessor(silence=60.0)
        
        assert processor.state_size == 0
        
        for i in range(3):
            event = OkoEvent(
                type="http_error",
                message=f"HTTP {i}",
                context={"path": f"/api/test{i}", "status_code": 500 + i},
            )
            processor.should_send(event)
        
        assert processor.state_size == 3


class TestDeduplicationProcessorRepr:
    """Test processor string representation."""

    def test_repr(self):
        """Test repr includes silence and tracked count."""
        processor = DeduplicationProcessor(silence=300.0)
        
        r = repr(processor)
        
        assert "DeduplicationProcessor" in r
        assert "silence" in r
        assert "tracked" in r
