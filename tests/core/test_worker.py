"""
Tests for OkoWorker.
"""
import pytest
import time
import threading

from oko.core.event import OkoEvent
from oko.core.queue import OkoQueue
from oko.core.worker import OkoWorker


class TestOkoWorkerCreation:
    """Test OkoWorker creation."""

    def test_create_worker(self):
        """Test creating a worker."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.5,
        )
        
        assert worker.is_running is False
        assert worker._batch_size == 10
        assert worker._poll_interval == 0.5


class TestOkoWorkerLifecycle:
    """Test worker start/stop."""

    def test_start_worker(self):
        """Test starting the worker."""
        queue = OkoQueue()
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        worker.start()
        
        try:
            assert worker.is_running is True
        finally:
            worker.stop(timeout=2.0)

    def test_stop_worker(self):
        """Test stopping the worker."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        worker.start()
        time.sleep(0.2)
        worker.stop(timeout=2.0)
        
        assert worker.is_running is False

    def test_double_start_does_nothing(self):
        """Test that starting an already running worker does nothing."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        worker.start()
        first_thread_id = worker._thread.ident
        worker.start()  # Should not raise
        second_thread_id = worker._thread.ident
        
        assert first_thread_id == second_thread_id
        
        worker.stop(timeout=2.0)


class TestOkoWorkerProcessing:
    """Test worker event processing."""

    def test_process_single_event(self):
        """Test processing a single event."""
        queue = OkoQueue()
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        event = OkoEvent(type="error", message="test")
        queue.put(event)
        
        worker.start()
        time.sleep(0.3)  # Wait for processing
        worker.stop(timeout=2.0)
        
        assert len(processed) == 1
        assert processed[0].message == "test"

    def test_process_batch_events(self):
        """Test processing multiple events."""
        queue = OkoQueue()
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(5)
        ]
        for e in events:
            queue.put(e)
        
        worker.start()
        time.sleep(0.3)
        worker.stop(timeout=2.0)
        
        assert len(processed) == 5

    def test_handler_exception_does_not_crash_worker(self):
        """Test that exceptions in handler don't crash worker."""
        queue = OkoQueue()
        
        def handler(events):
            raise ValueError("Handler error")
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=0.1,
        )
        
        event = OkoEvent(type="error", message="test")
        queue.put(event)
        
        worker.start()
        time.sleep(0.3)
        
        # Worker should still be running despite handler error
        assert worker.is_running is True
        
        worker.stop(timeout=2.0)

    def test_graceful_shutdown_flushes_queue(self):
        """Test that stop flushes remaining events."""
        queue = OkoQueue()
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
            poll_interval=10.0,  # Long poll interval
        )
        
        # Put events after worker starts
        worker.start()
        time.sleep(0.2)
        
        events = [
            OkoEvent(type="error", message=f"msg{i}")
            for i in range(3)
        ]
        for e in events:
            queue.put(e)
        
        # Stop should flush remaining
        worker.stop(timeout=2.0)
        
        # All events should be processed
        assert len(processed) == 3


class TestOkoWorkerConfiguration:
    """Test worker configuration options."""

    def test_custom_batch_size(self):
        """Test custom batch size."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=5,
        )
        
        assert worker._batch_size == 5

    def test_custom_poll_interval(self):
        """Test custom poll interval."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            poll_interval=2.0,
        )
        
        assert worker._poll_interval == 2.0


class TestOkoWorkerRepr:
    """Test worker string representation."""

    def test_repr_running(self):
        """Test repr when running."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
        )
        
        r = repr(worker)
        
        assert "OkoWorker" in r

    def test_repr_stopped(self):
        """Test repr when stopped."""
        queue = OkoQueue()
        
        def handler(events):
            pass
        
        worker = OkoWorker(
            queue=queue,
            handler=handler,
            batch_size=10,
        )
        
        r = repr(worker)
        
        assert "OkoWorker" in r
