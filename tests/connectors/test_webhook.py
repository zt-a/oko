"""
Tests for WebhookConnector.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from oko.core.event import OkoEvent
from oko.connectors.webhook import WebhookConnector


class TestWebhookConnectorCreation:
    """Test WebhookConnector creation."""

    def test_create_connector(self):
        """Test creating a connector."""
        connector = WebhookConnector(url="https://example.com/hook")
        
        assert connector._url == "https://example.com/hook"

    def test_create_connector_with_headers(self):
        """Test creating connector with custom headers."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            headers={"Authorization": "Bearer token"},
        )
        
        assert connector._headers["Authorization"] == "Bearer token"

    def test_create_connector_with_timeout(self):
        """Test creating connector with custom timeout."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            timeout=5.0,
        )
        
        assert connector._timeout == 5.0

    def test_create_connector_custom_method(self):
        """Test creating connector with custom HTTP method."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            method="PUT",
        )
        
        assert connector._method == "PUT"


class TestWebhookConnectorBuildPayload:
    """Test payload building."""

    @pytest.mark.asyncio
    async def test_build_payload(self):
        """Test building payload from event."""
        connector = WebhookConnector(url="https://example.com/hook")
        
        event = OkoEvent(
            type="error",
            message="Test error",
            stack="Traceback",
            context={"path": "/api/test"},
        )
        
        payload = connector._build_payload(event)
        
        assert payload["type"] == "error"
        assert payload["message"] == "Test error"
        assert payload["stack"] == "Traceback"
        assert payload["context"]["path"] == "/api/test"
        assert "timestamp" in payload
        assert "fingerprint" in payload


class TestWebhookConnectorSend:
    """Test sending webhooks."""

    @pytest.mark.asyncio
    async def test_send_event(self):
        """Test sending an event."""
        connector = WebhookConnector(url="https://example.com/hook")
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await connector.send(event)

    @pytest.mark.asyncio
    async def test_send_uses_post_by_default(self):
        """Test that POST is used by default."""
        connector = WebhookConnector(url="https://example.com/hook")
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await connector.send(event)
            
            # Check that request was called with POST
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args[1]["method"] == "POST"

    @pytest.mark.asyncio
    async def test_send_uses_custom_method(self):
        """Test that custom method is used."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            method="PUT",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await connector.send(event)
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args[1]["method"] == "PUT"

    @pytest.mark.asyncio
    async def test_send_includes_headers(self):
        """Test that headers are included in request."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            headers={"X-Custom": "value"},
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await connector.send(event)
            
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            assert call_args[1]["headers"]["X-Custom"] == "value"

    @pytest.mark.asyncio
    async def test_send_handles_timeout(self):
        """Test handling timeout."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            timeout=0.1,
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            
            # Should not raise
            await connector.send(event)

    @pytest.mark.asyncio
    async def test_send_handles_http_error(self):
        """Test handling HTTP errors."""
        connector = WebhookConnector(
            url="https://example.com/hook",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "error",
                    request=MagicMock(),
                    response=mock_response,
                )
            )
            
            # Should not raise
            await connector.send(event)

    @pytest.mark.asyncio
    async def test_send_handles_generic_error(self):
        """Test handling generic errors."""
        connector = WebhookConnector(
            url="https://example.com/hook",
        )
        
        event = OkoEvent(
            type="error",
            message="Test error",
        )
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=Exception("generic error")
            )
            
            # Should not raise
            await connector.send(event)


class TestWebhookConnectorRepr:
    """Test connector string representation."""

    def test_repr(self):
        """Test repr includes URL and method."""
        connector = WebhookConnector(
            url="https://example.com/hook",
            method="POST",
        )
        
        r = repr(connector)
        
        assert "WebhookConnector" in r
        assert "https://example.com/hook" in r
        assert "POST" in r
