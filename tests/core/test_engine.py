"""
Tests for OkoEngine.
"""
import pytest
import time
import traceback

from oko.core.event import OkoEvent
from oko.core.queue import OkoQueue
from oko.core.worker import OkoWorker
from oko.core.engine import OkoEngine


class TestOkoEngineCreation:
    """Test OkoEngine creation."""

    def test_create_engine(self):
        """Test creating an engine."""
        def handler(events):
            pass
        
        engine = OkoEngine(handler=handler)
        
        assert engine.is_running is False
        assert engine._queue is not None
        assert engine._worker is not None

    def test_create_engine_with_custom_params(self):
        """Test creating engine with custom parameters."""
        def handler(events):
            pass
        
        engine = OkoEngine(
            handler=handler,
            queue_maxsize=100,
            batch_size=5,
            poll_interval=0.5,
        )
        
        assert engine._worker._batch_size == 5
        assert engine._worker._poll_interval == 0.5


class TestOkoEngineLifecycle:
    """Test engine start/stop."""

    def test_start_engine(self):
        """Test starting the engine."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            assert engine.is_running is True
            assert engine._worker.is_running is True
        finally:
            engine.stop(timeout=2.0)

    def test_stop_engine(self):
        """Test stopping the engine."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        time.sleep(0.2)
        engine.stop(timeout=2.0)
        
        assert engine.is_running is False

    def test_graceful_shutdown(self):
        """Test graceful shutdown processes events."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler, poll_interval=10.0)
        engine.start()
        time.sleep(0.2)
        
        # Add events before stop
        for i in range(3):
            engine.capture_exception(
                ValueError(f"error {i}"),
                context={"index": i}
            )
        
        time.sleep(0.1)
        engine.stop(timeout=2.0)
        
        # Events should be processed during shutdown
        assert len(processed) >= 1


class TestOkoEngineCapture:
    """Test engine capture methods."""

    def test_capture_exception(self):
        """Test capturing an exception."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            try:
                raise ValueError("test error")
            except ValueError as exc:
                engine.capture_exception(exc, context={"test": True})
            
            time.sleep(0.3)
            
            assert len(processed) >= 1
            event = processed[0]
            assert event.type == "error"
            assert "ValueError" in event.message
        finally:
            engine.stop(timeout=2.0)

    def test_capture_exception_with_context(self):
        """Test capturing exception with context."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            try:
                raise ValueError("test")
            except ValueError as exc:
                engine.capture_exception(
                    exc, context={"user_id": 123, "path": "/api/test"}
                )
            
            time.sleep(0.3)
            
            event = processed[0]
            assert event.context["user_id"] == 123
            assert event.context["path"] == "/api/test"
        finally:
            engine.stop(timeout=2.0)

    def test_capture_http_error(self):
        """Test capturing HTTP error."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            engine.capture_http_error(
                status_code=500,
                method="POST",
                path="/api/problems",
                context={"client_ip": "127.0.0.1"},
            )
            
            time.sleep(0.3)
            
            assert len(processed) == 1
            event = processed[0]
            assert event.type == "http_error"
            assert event.context["status_code"] == 500
            assert event.context["method"] == "POST"
            assert event.context["path"] == "/api/problems"
            assert event.context["client_ip"] == "127.0.0.1"
        finally:
            engine.stop(timeout=2.0)

    def test_capture_http_error_default_context(self):
        """Test HTTP error with merged context."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            engine.capture_http_error(
                status_code=404,
                method="GET",
                path="/api/notfound",
                context={"extra": "value"},
            )
            
            time.sleep(0.3)
            
            event = processed[0]
            assert event.context["status_code"] == 404
            assert event.context["extra"] == "value"
        finally:
            engine.stop(timeout=2.0)

    def test_capture_log(self):
        """Test capturing a log message."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            engine.capture_log(
                message="Test log message",
                level="warning",
            )
            
            time.sleep(0.3)
            
            assert len(processed) == 1
            event = processed[0]
            assert event.type == "log"
            assert event.message == "Test log message"
            assert event.context["level"] == "warning"
        finally:
            engine.stop(timeout=2.0)

    def test_capture_log_with_context(self):
        """Test capturing log with custom context."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            engine.capture_log(
                message="User logged in",
                level="info",
                context={"user_id": 42},
            )
            
            time.sleep(0.3)
            
            event = processed[0]
            assert event.context["user_id"] == 42
            assert event.context["level"] == "info"
        finally:
            engine.stop(timeout=2.0)


class TestOkoEngineQueueIntegration:
    """Test engine queue properties."""

    def test_queue_size(self):
        """Test queue size property."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            # Add events without processing
            for i in range(3):
                engine.capture_log(f"message {i}")
            
            time.sleep(0.1)
            
            assert engine._queue.size >= 0
        finally:
            engine.stop(timeout=2.0)


class TestOkoEngineRepr:
    """Test engine string representation."""

    def test_repr_running(self):
        """Test repr when running."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        engine.start()
        
        try:
            r = repr(engine)
            assert "OkoEngine" in r
            assert "running" in r
        finally:
            engine.stop(timeout=2.0)

    def test_repr_stopped(self):
        """Test repr when stopped."""
        processed = []
        
        def handler(events):
            processed.extend(events)
        
        engine = OkoEngine(handler=handler)
        
        r = repr(engine)
        assert "OkoEngine" in r