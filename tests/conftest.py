"""
Shared fixtures for OKO tests.
"""
import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

from oko.core.event import OkoEvent
from oko.storage.sqlite import SQLiteStorage


@pytest.fixture
def sample_event():
    """Create a sample OkoEvent for testing."""
    return OkoEvent(
        type="error",
        message="Test error message",
        stack="Traceback (most recent call last):\n  File test.py line 1",
        context={"path": "/api/test", "method": "GET"},
    )


@pytest.fixture
def sample_events():
    """Create multiple sample OkoEvents for testing."""
    return [
        OkoEvent(
            type="error",
            message="Error 1",
            stack="Traceback",
            context={"path": "/api/test1", "method": "GET"},
        ),
        OkoEvent(
            type="http_error",
            message="HTTP 500 POST /api/test2",
            context={"path": "/api/test2", "method": "POST", "status_code": 500},
        ),
        OkoEvent(
            type="log",
            message="Info log",
            context={"level": "info"},
        ),
    ]


@pytest.fixture
def memory_storage():
    """Create an in-memory SQLite storage for testing."""
    storage = SQLiteStorage(":memory:")
    return storage


@pytest.fixture
def temp_db_storage():
    """Create a temporary file-based SQLite storage for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    storage = SQLiteStorage(db_path)
    yield storage
    
    # Cleanup
    try:
        os.unlink(db_path)
        os.unlink(db_path + "-wal") if os.path.exists(db_path + "-wal") else None
        os.unlink(db_path + "-shm") if os.path.exists(db_path + "-shm") else None
    except Exception:
        pass


@pytest.fixture
def mock_connector():
    """Create a mock connector for testing."""
    connector = AsyncMock()
    connector.send = AsyncMock(return_value=None)
    connector.send_batch = AsyncMock(return_value=None)
    return connector


@pytest.fixture
def sample_context():
    """Sample context dictionary for testing."""
    return {
        "path": "/api/test",
        "method": "GET",
        "status_code": 500,
        "client_ip": "127.0.0.1",
        "user_agent": "test-agent",
    }
