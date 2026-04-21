"""
Tests for EnrichmentProcessor.
"""
import pytest
import platform
import sys

from oko.core.event import OkoEvent
from oko.pipeline.enrichment import EnrichmentProcessor


class TestEnrichmentProcessorCreation:
    """Test EnrichmentProcessor creation."""

    def test_create_processor_without_params(self):
        """Test creating processor without parameters."""
        processor = EnrichmentProcessor()
        
        assert processor is not None

    def test_create_processor_with_params(self):
        """Test creating processor with custom parameters."""
        processor = EnrichmentProcessor(
            project="testproject",
            environment="production",
            version="1.0.0",
        )
        
        context = processor.static_context
        assert context["project"] == "testproject"
        assert context["environment"] == "production"
        assert context["version"] == "1.0.0"

    def test_create_processor_with_extra(self):
        """Test creating processor with extra context."""
        processor = EnrichmentProcessor(
            project="testproject",
            extra={"team": "backend", "region": "us-east"},
        )
        
        context = processor.static_context
        assert context["team"] == "backend"
        assert context["region"] == "us-east"


class TestEnrichmentProcessorEnrich:
    """Test event enrichment."""

    def test_enrich_basic_event(self):
        """Test enriching a basic event."""
        processor = EnrichmentProcessor(
            project="testproject",
            environment="test",
        )
        
        event = OkoEvent(type="error", message="test")
        result = processor.enrich(event)
        
        assert result.context["project"] == "testproject"
        assert result.context["environment"] == "test"

    def test_enrich_adds_python_version(self):
        """Test that enrichment adds Python version."""
        processor = EnrichmentProcessor()
        
        event = OkoEvent(type="error", message="test")
        processor.enrich(event)
        
        assert "python" in event.context
        assert event.context["python"] == sys.version.split()[0]

    def test_enrich_adds_os(self):
        """Test that enrichment adds OS info."""
        processor = EnrichmentProcessor()
        
        event = OkoEvent(type="error", message="test")
        processor.enrich(event)
        
        assert "os" in event.context

    def test_enrich_does_not_overwrite_existing(self):
        """Test that enrichment doesn't overwrite existing context."""
        processor = EnrichmentProcessor(
            project="processorproject",
            environment="production",
        )
        
        event = OkoEvent(
            type="error",
            message="test",
            context={
                "project": "eventproject",  # Already exists
                "custom": "value",
            }
        )
        processor.enrich(event)
        
        assert event.context["project"] == "eventproject"  # Not overwritten
        assert event.context["custom"] == "value"  # Preserved
        assert event.context["environment"] == "production"  # Added

    def test_enrich_returns_same_event(self):
        """Test that enrich returns the same event object."""
        processor = EnrichmentProcessor()
        
        event = OkoEvent(type="error", message="test")
        result = processor.enrich(event)
        
        assert result is event  # Same object, mutated in place


class TestEnrichmentProcessorStaticContext:
    """Test static context property."""

    def test_static_context_includes_all(self):
        """Test static context includes all configured values."""
        processor = EnrichmentProcessor(
            project="myproject",
            environment="dev",
            version="2.0.0",
            extra={"custom": "value"},
        )
        
        context = processor.static_context
        
        assert "project" in context
        assert "environment" in context
        assert "version" in context
        assert "custom" in context
        assert "python" in context
        assert "os" in context

    def test_static_context_returns_copy(self):
        """Test that static_context returns a copy."""
        processor = EnrichmentProcessor(project="test")
        
        context = processor.static_context
        context["new_key"] = "new_value"
        
        # Original should not be modified
        assert "new_key" not in processor.static_context


class TestEnrichmentProcessorRepr:
    """Test processor string representation."""

    def test_repr(self):
        """Test repr includes added keys."""
        processor = EnrichmentProcessor(
            project="test",
            environment="prod",
        )
        
        r = repr(processor)
        
        assert "EnrichmentProcessor" in r
        assert "project" in r
        assert "environment" in r
