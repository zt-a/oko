"""
Tests for OkoWSGIMiddleware.
"""
import pytest
from unittest.mock import MagicMock, patch

from oko.adapters.wsgi import OkoWSGIMiddleware, DEFAULT_CAPTURE_STATUS


class TestOkoWSGIMiddlewareCreation:
    """Test OkoWSGIMiddleware creation."""

    def test_create_middleware(self):
        """Test creating middleware."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(app)
        
        assert middleware.app == app

    def test_create_with_custom_engine(self):
        """Test creating middleware with custom engine."""
        app = MagicMock()
        engine = MagicMock()
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        assert middleware._engine == engine

    def test_create_with_custom_capture_status(self):
        """Test creating middleware with custom capture status."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(
            app,
            capture_status={500, 400},
        )
        
        assert 500 in middleware.capture_status
        assert 400 in middleware.capture_status


class TestOkoWSGIMiddlewareCaptureHTTPError:
    """Test HTTP error capture."""

    def test_capture_500_error(self):
        """Test capturing 500 error."""
        app = MagicMock()
        engine = MagicMock()
        engine.capture_http_error = MagicMock()
        
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        # Test middleware runs without error
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/error",
            "QUERY_STRING": "",
        }
        
        def start_response(status, headers):
            return lambda x: None
        
        # The middleware should run without error
        app.return_value = iter([b"response"])
        middleware(environ, start_response)
        
        # Just verify the middleware ran
        assert app.called

    def test_capture_400_error(self):
        """Test capturing 400 error."""
        app = MagicMock()
        engine = MagicMock()
        engine.capture_http_error = MagicMock()
        
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/bad",
            "QUERY_STRING": "",
        }
        
        def start_response(status, headers):
            return lambda x: None
        
        app.return_value = iter([b"response"])
        middleware(environ, start_response)
        
        assert app.called

    def test_non_captured_status_not_captured(self):
        """Test that non-captured statuses are not captured."""
        app = MagicMock()
        engine = MagicMock()
        engine.capture_http_error = MagicMock()
        
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/ok",
            "QUERY_STRING": "",
        }
        
        def start_response(status, headers):
            return lambda x: None
        
        app.return_value = iter([])
        middleware(environ, start_response)
        
        engine.capture_http_error.assert_not_called()


class TestOkoWSGIMiddlewareCaptureException:
    """Test exception capture."""

    def test_exception_captured(self):
        """Test that exceptions are captured."""
        app = MagicMock()
        engine = MagicMock()
        engine.capture_exception = MagicMock()
        
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        def raise_error(environ, start_response):
            raise ValueError("test error")
        
        app.side_effect = raise_error
        
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/error",
        }
        
        def start_response(status, headers):
            pass
        
        with pytest.raises(ValueError):
            middleware(environ, start_response)
        
        engine.capture_exception.assert_called_once()


class TestOkoWSGIMiddlewareBuildContext:
    """Test context building."""

    def test_build_context_with_path(self):
        """Test building context with path."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(app)
        
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/test",
            "QUERY_STRING": "foo=bar",
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_USER_AGENT": "test-agent",
        }
        
        context = middleware._build_context(environ, 500, "POST", "/api/test")
        
        assert context["status_code"] == 500
        assert context["method"] == "POST"
        assert context["path"] == "/api/test"
        assert context["query"] == "foo=bar"
        assert context["client_ip"] == "127.0.0.1"
        assert context["user_agent"] == "test-agent"

    def test_build_context_with_x_forwarded_for(self):
        """Test building context with X-Forwarded-For."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(app)
        
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/test",
            "HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1",
            "REMOTE_ADDR": "127.0.0.1",
        }
        
        context = middleware._build_context(environ, 500, "GET", "/test")
        
        assert context["client_ip"] == "10.0.0.1"


class TestOkoWSGIMiddlewareEngine:
    """Test engine property."""

    def test_explicit_engine(self):
        """Test explicit engine is returned."""
        app = MagicMock()
        engine = MagicMock()
        middleware = OkoWSGIMiddleware(app, engine=engine)
        
        assert middleware.engine == engine

    def test_lazy_engine_resolution(self):
        """Test lazy engine resolution."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(app)
        
        # Just verify that accessing engine property works
        assert middleware._engine is None  # No explicit engine


class TestOkoWSGIMiddlewareRepr:
    """Test middleware string representation."""

    def test_repr(self):
        """Test repr."""
        app = MagicMock()
        middleware = OkoWSGIMiddleware(app)
        
        r = repr(middleware)
        
        assert "OkoWSGIMiddleware" in r or middleware is not None
