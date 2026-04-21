"""
Tests for TelegramConnector.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from oko.core.event import OkoEvent
from oko.connectors.telegram import TelegramConnector


class TestTelegramConnectorCreation:
    """Test TelegramConnector creation."""

    def test_create_connector(self):
        """Test creating a connector."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        assert connector._token == "test_token"
        assert connector._chat_id == "test_chat_id"

    def test_create_connector_with_dashboard_url(self):
        """Test creating connector with dashboard URL."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
            dashboard_url="https://myapp.com",
        )
        
        assert connector._dashboard_url == "https://myapp.com"

    def test_dashboard_url_strip_trailing_slash(self):
        """Test that trailing slash is stripped from dashboard URL."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
            dashboard_url="https://myapp.com/",
        )
        
        assert connector._dashboard_url == "https://myapp.com"


class TestTelegramConnectorFormat:
    """Test message formatting."""

    @pytest.mark.asyncio
    async def test_format_server_error(self):
        """Test formatting server error message."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="error",
            message="ValueError: test error",
            stack="Traceback...\n  File test.py",
            context={"project": "myproject", "environment": "production"},
        )
        
        text = connector._format(event)
        
        assert "🔔" in text  # Regular error type uses default icon
        assert "OKO ALERT" in text
        assert "myproject" in text
        assert "PRODUCTION" in text  # Environment in header

    @pytest.mark.asyncio
    async def test_format_client_error(self):
        """Test formatting client error message."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="http_error",
            message="HTTP 404",
            context={"status_code": 404, "path": "/api/notfound", "method": "GET"},
        )
        
        text = connector._format(event)
        
        assert "⚠️" in text

    @pytest.mark.asyncio
    async def test_format_log(self):
        """Test formatting log message."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="log",
            message="Info message",
            context={"level": "info"},
        )
        
        text = connector._format(event)
        
        assert "ℹ️" in text

    @pytest.mark.asyncio
    async def test_format_with_dashboard_link(self):
        """Test formatting with dashboard link."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
            dashboard_url="https://myapp.com",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
            context={"id": 42},
        )
        
        text = connector._format(event)
        
        assert "https://myapp.com/oko/42" in text
        assert "🔗" in text

    @pytest.mark.asyncio
    async def test_format_with_environment(self):
        """Test formatting includes environment."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
            context={"environment": "production"},
        )
        
        text = connector._format(event)
        
        assert "PRODUCTION" in text

    @pytest.mark.asyncio
    async def test_format_stack_trace(self):
        """Test formatting includes stack trace."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
            stack="Traceback (most recent call last):\n  File test.py line 1",
        )
        
        text = connector._format(event)
        
        assert "Traceback" in text
        assert "```python" in text


class TestTelegramConnectorIcon:
    """Test icon selection."""

    @pytest.mark.asyncio
    async def test_icon_server_error(self):
        """Test icon for server error."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="http_error",
            message="500",
            context={"status_code": 500},
        )
        
        assert connector._icon(event) == "❌"

    @pytest.mark.asyncio
    async def test_icon_client_error(self):
        """Test icon for client error."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="http_error",
            message="404",
            context={"status_code": 404},
        )
        
        assert connector._icon(event) == "⚠️"

    @pytest.mark.asyncio
    async def test_icon_log(self):
        """Test icon for log."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="log",
            message="log",
            context={"level": "info"},
        )
        
        assert connector._icon(event) == "ℹ️"


class TestTelegramConnectorEscape:
    """Test markdown escaping."""

    @pytest.mark.asyncio
    async def test_escape_special_chars(self):
        """Test escaping special markdown characters."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        text = "test_underscore *asterisk* `code`"
        
        escaped = connector._escape(text)
        
        assert "\\_" in escaped
        assert "\\*" in escaped
        assert "\\`" in escaped


class TestTelegramConnectorSend:
    """Test sending messages."""

    @pytest.mark.asyncio
    async def test_send_event(self):
        """Test sending an event."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            await connector.send(event)

    @pytest.mark.asyncio
    async def test_send_handles_timeout(self):
        """Test handling timeout."""
        import httpx
        
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
            timeout=0.1,
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            
            # Should not raise
            await connector.send(event)

    @pytest.mark.asyncio
    async def test_send_handles_http_error(self):
        """Test handling HTTP errors."""
        import httpx
        
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "error",
                    request=MagicMock(),
                    response=mock_response,
                )
            )
            
            # Should not raise
            await connector.send(event)


class TestTelegramConnectorRepr:
    """Test connector string representation."""

    def test_repr(self):
        """Test repr includes chat_id."""
        connector = TelegramConnector(
            token="test_token",
            chat_id="test_chat_id",
        )
        
        r = repr(connector)
        
        assert "TelegramConnector" in r
        assert "test_chat_id" in r