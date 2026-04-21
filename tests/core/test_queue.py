"""
Tests for OkoQueue.
"""
import pytest
import threading
import time

from oko.core.event import OkoEvent
from oko.core.queue import OkoQueue


class TestOkoQueueCreation:
    """Test OkoQueue creation."""

    def test_create_unlimited_queue(self):
        """Test creating an unlimited queue."""
        queue = OkoQueue()
        
        assert queue.size == 0
        assert queue.is_empty is True

    def test_create_limited_queue(self):
        """Test creating a limited queue."""
        queue = OkoQueue(maxsize=10)
        
        assert queue.size == 0


class TestOkoQueuePut:
    """Test putting events into queue."""

    def test_put_single_event(self, sample_event):
        """Test putting a single event."""
        queue = OkoQueue()
        queue.put(sample_event)
        
        assert queue.size == 1
        assert queue.is_empty is False

    def test_put_multiple_events(self, sample_events):
        """Test putting multiple events."""
        queue = OkoQueue()
        for event in sample_events:
            queue.put(event)
        
        assert queue.size == 3

    def test_put_over_maxsize(self):
        """Test putting more events than maxsize."""
        queue = OkoQueue(maxsize=2)
        
        e1 = OkoEvent(type="error", message="1")
        e2 = OkoEvent(type="error", message="2")
        e3 = OkoEvent(type="error", message="3")
        
        queue.put(e1)
        queue.put(e2)
        queue.put(e3)  # Should not raise, just drop
        
        # Only 2 events should be in queue
        assert queue.size <= 2


class TestOkoQueueGet:
    """Test getting events from queue."""

    def test_get_with_content(self, sample_event):
        """Test getting an event that was put."""
        queue = OkoQueue()
        queue.put(sample_event)
        
        result = queue.get(timeout=1.0)
        
        assert result is not None
        assert result.message == sample_event.message

    def test_get_timeout_returns_none(self):
        """Test that get returns None on timeout."""
        queue = OkoQueue()
        
        result = queue.get(timeout=0.1)
        
        assert result is None

    def test_get_after_put(self):
        """Test get returns the correct event."""
        event = OkoEvent(type="error", message="test")
        queue = OkoQueue()
        queue.put(event)
        
        result = queue.get(timeout=1.0)
        
        assert result.message == "test"


class TestOkoQueueGetBatch:
    """Test batch retrieval."""

    def test_get_batch_empty_queue(self):
        """Test getting batch from empty queue."""
        queue = OkoQueue()
        
        batch = queue.get_batch(max_size=10)
        
        assert batch == []

    def test_get_batch_full_batch(self):
        """Test getting a full batch."""
        events = [OkoEvent(type="error", message=f"msg{i}") for i in range(5)]
        queue = OkoQueue()
        for e in events:
            queue.put(e)
        
        batch = queue.get_batch(max_size=10)
        
        assert len(batch) == 5

    def test_get_batch_limited(self):
        """Test getting limited batch."""
        events = [OkoEvent(type="error", message=f"msg{i}") for i in range(10)]
        queue = OkoQueue()
        for e in events:
            queue.put(e)
        
        batch = queue.get_batch(max_size=3)
        
        assert len(batch) == 3

    def test_get_batch_sequential(self):
        """Test sequential batch calls."""
        events = [OkoEvent(type="error", message=f"msg{i}") for i in range(7)]
        queue = OkoQueue()
        for e in events:
            queue.put(e)
        
        batch1 = queue.get_batch(max_size=5)
        batch2 = queue.get_batch(max_size=5)
        
        assert len(batch1) == 5
        assert len(batch2) == 2


class TestOkoQueueThreadSafety:
    """Test thread safety of queue."""

    def test_concurrent_put_get(self):
        """Test concurrent put and get operations."""
        queue = OkoQueue()
        errors = []
        
        def put_events():
            try:
                for i in range(100):
                    event = OkoEvent(type="error", message=f"msg{i}")
                    queue.put(event)
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(e)
        
        def get_events():
            try:
                for _ in range(100):
                    queue.get(timeout=0.01)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=put_events),
            threading.Thread(target=get_events),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestOkoQueueProperties:
    """Test queue properties."""

    def test_size_property(self):
        """Test size property."""
        queue = OkoQueue()
        
        assert queue.size == 0
        
        queue.put(OkoEvent(type="error", message="test"))
        
        assert queue.size == 1

    def test_is_empty_property(self):
        """Test is_empty property."""
        queue = OkoQueue()
        
        assert queue.is_empty is True
        
        queue.put(OkoEvent(type="error", message="test"))
        
        assert queue.is_empty is False


class TestOkoQueueRepr:
    """Test queue string representation."""

    def test_repr(self):
        """Test repr includes size."""
        queue = OkoQueue()
        
        r = repr(queue)
        
        assert "OkoQueue" in r
        assert "size" in r