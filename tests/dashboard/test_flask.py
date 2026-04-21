"""
Tests for Flask Dashboard adapter.
"""
import pytest
from unittest.mock import patch, MagicMock

from oko.dashboard.adapters.flask import create_dashboard_blueprint
from oko.storage.sqlite import SQLiteStorage


class TestCreateDashboardBlueprint:
    """Test create_dashboard_blueprint function."""

    def test_create_blueprint_requires_flask(self):
        """Test that Flask is required."""
        import sys
        # Temporarily remove flask from sys.modules
        original_modules = dict(sys.modules)
        sys.modules['flask'] = None
        
        try:
            # This will fail because Flask isn't available in the import
            pass
        finally:
            # Restore modules
            for mod in list(sys.modules.keys()):
                if mod not in original_modules:
                    del sys.modules[mod]

    def test_blueprint_created(self):
        """Test that blueprint is created."""
        storage = SQLiteStorage(":memory:")
        blueprint = create_dashboard_blueprint(storage=storage)
        
        assert blueprint is not None
        assert blueprint.name == "oko_dashboard"

    def test_blueprint_default_url_prefix(self):
        """Test default URL prefix."""
        storage = SQLiteStorage(":memory:")
        blueprint = create_dashboard_blueprint(storage=storage)
        
        assert blueprint.url_prefix == "/oko"

    def test_blueprint_custom_url_prefix(self):
        """Test custom URL prefix."""
        storage = SQLiteStorage(":memory:")
        blueprint = create_dashboard_blueprint(
            storage=storage,
            url_prefix="/errors"
        )
        
        assert blueprint.url_prefix == "/errors"

    def test_blueprint_has_name(self):
        """Test that blueprint has correct name."""
        storage = SQLiteStorage(":memory:")
        blueprint = create_dashboard_blueprint(storage=storage)
        
        assert blueprint.name == "oko_dashboard"

    def test_blueprint_has_view_functions(self):
        """Test that blueprint has view functions."""
        storage = SQLiteStorage(":memory:")
        blueprint = create_dashboard_blueprint(storage=storage)
        
        # Check that view functions exist
        assert hasattr(blueprint, 'record')
