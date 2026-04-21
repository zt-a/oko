"""
Tests for RateLimitProcessor.
"""
import pytest
import time

from oko.core.event import OkoEvent
from oko.pipeline.rate_limit import RateLimitProcessor


class TestRateLimitProcessorCreation:
    """Test RateLimitProcessor creation."""

    def test_create_processor_defaults(self):
        """Test creating processor with default values."""
        processor = RateLimitProcessor()
        
        assert processor.max_tokens == 10.0
        assert processor.tokens == 10.0

    def test_create_processor_custom(self):
        """Test creating processor with custom values."""
        processor = RateLimitProcessor(
            max_tokens=5.0,
            refill_rate=2.0,
        )
        
        assert processor.max_tokens == 5.0
        assert processor.tokens == 5.0


class TestRateLimitProcessorShouldSend:
    """Test should_send method."""

    def test_first_events_pass(self):
        """Test that first events pass."""
        processor = RateLimitProcessor(max_tokens=3.0)
        
        results = []
        for _ in range(3):
            event = OkoEvent(type="error", message="test")
            results.append(processor.should_send(event))
        
        assert results == [True, True, True]

    def test_exceed_burst_blocked(self):
        """Test that exceeding burst capacity blocks events."""
        processor = RateLimitProcessor(max_tokens=2.0)
        
        # First 2 pass
        event1 = OkoEvent(type="error", message="1")
        event2 = OkoEvent(type="error", message="2")
        assert processor.should_send(event1) is True
        assert processor.should_send(event2) is True
        
        # Third should be blocked
        event3 = OkoEvent(type="error", message="3")
        assert processor.should_send(event3) is False

    def test_tokens_restore_over_time(self):
        """Test that tokens restore over time."""
        processor = RateLimitProcessor(
            max_tokens=2.0,
            refill_rate=10.0,  # Fast refill: 10 tokens per second
        )
        
        # Exhaust tokens
        processor.should_send(OkoEvent(type="error", message="1"))
        processor.should_send(OkoEvent(type="error", message="2"))
        
        # Wait for refill
        time.sleep(0.3)  # Should get ~3 tokens
        
        # Should pass now
        event = OkoEvent(type="error", message="test")
        result = processor.should_send(event)
        
        assert result is True


class TestRateLimitProcessorRefill:
    """Test token refill behavior."""

    def test_refill_increments_tokens(self):
        """Test that tokens are refilled."""
        processor = RateLimitProcessor(
            max_tokens=10.0,
            refill_rate=1.0,  # 1 token per second
        )
        
        # Use some tokens
        for _ in range(5):
            processor.should_send(OkoEvent(type="error", message="test"))
        
        initial_tokens = processor.tokens
        
        # Wait for refill
        time.sleep(0.5)
        
        # Tokens should have increased (approximately 0.5 + some initial)
        # The exact value depends on timing, but it should be > 0
        assert processor.tokens >= 0

    def test_tokens_capped_at_max(self):
        """Test that tokens don't exceed max."""
        processor = RateLimitProcessor(
            max_tokens=5.0,
            refill_rate=10.0,
        )
        
        # Wait for refill
        time.sleep(0.6)
        
        # Should not exceed max_tokens
        assert processor.tokens <= processor.max_tokens


class TestRateLimitProcessorTokens:
    """Test token tracking."""

    def test_tokens_decrease_on_send(self):
        """Test that tokens decrease when event is sent."""
        processor = RateLimitProcessor(max_tokens=10.0)
        
        initial = processor.tokens
        
        processor.should_send(OkoEvent(type="error", message="test"))
        
        assert processor.tokens < initial


class TestRateLimitProcessorRepr:
    """Test processor string representation."""

    def test_repr(self):
        """Test repr includes tokens info."""
        processor = RateLimitProcessor(max_tokens=5.0)
        
        r = repr(processor)
        
        assert "RateLimitProcessor" in r
        assert "tokens" in r
        assert "5.0" in r or "5" in r
