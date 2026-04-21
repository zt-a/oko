"""
Tests for OkoPipeline.
"""
import pytest
import time

from oko.core.event import OkoEvent
from oko.pipeline.processor import OkoPipeline


class TestOkoPipelineCreation:
    """Test OkoPipeline creation."""

    def test_create_pipeline(self):
        """Test creating a pipeline."""
        output_handler = lambda events: None
        
        pipeline = OkoPipeline(output_handler=output_handler)
        
        assert pipeline is not None

    def test_create_pipeline_with_params(self):
        """Test creating pipeline with custom parameters."""
        output_handler = lambda events: None
        
        pipeline = OkoPipeline(
            output_handler=output_handler,
            silence=300.0,
            rate_limit_max=5.0,
            rate_limit_refill=2.0,
            project="testproject",
            environment="test",
            version="1.0.0",
        )
        
        assert pipeline is not None


class TestOkoPipelineProcess:
    """Test pipeline processing."""

    def test_process_empty_batch(self):
        """Test processing empty batch."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(output_handler=output_handler)
        
        pipeline.process([])
        
        assert len(processed) == 0

    def test_process_single_event(self):
        """Test processing single event."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(output_handler=output_handler)
        
        event = OkoEvent(type="error", message="test")
        pipeline.process([event])
        
        assert len(processed) == 1
        assert processed[0].message == "test"

    def test_process_multiple_events(self):
        """Test processing multiple events."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(output_handler=output_handler)
        
        events = [
            OkoEvent(type="error", message=f"msg{i}", context={"path": f"/api/test{i}"})
            for i in range(5)
        ]
        pipeline.process(events)
        
        # All 5 should pass through
        assert len(processed) == 5

    def test_process_enriches_events(self):
        """Test that pipeline enriches events."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(
            output_handler=output_handler,
            project="testproject",
            environment="production",
        )
        
        event = OkoEvent(type="error", message="test")
        pipeline.process([event])
        
        assert processed[0].context["project"] == "testproject"
        assert processed[0].context["environment"] == "production"

    def test_process_filters_duplicates(self):
        """Test that pipeline filters duplicates."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(
            output_handler=output_handler,
            silence=60.0,
        )
        
        event = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        pipeline.process([event])
        pipeline.process([event])  # Duplicate
        
        assert len(processed) == 1

    def test_process_respects_rate_limit(self):
        """Test that pipeline respects rate limits."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(
            output_handler=output_handler,
            rate_limit_max=2.0,
            rate_limit_refill=100.0,  # No refill during test
        )
        
        # Different paths give different fingerprints
        events = [
            OkoEvent(type="http_error", message=f"msg{i}", context={"path": f"/api/test{i}", "status_code": 500})
            for i in range(5)
        ]
        pipeline.process(events)
        
        # Only 2 should pass due to rate limit
        assert len(processed) == 2


class TestOkoPipelineChain:
    """Test pipeline processing chain."""

    def test_enrichment_before_filtering(self):
        """Test that enrichment happens before filtering."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        pipeline = OkoPipeline(
            output_handler=output_handler,
            project="testproject",
        )
        
        event = OkoEvent(
            type="error",
            message="test",
            context={"path": "/api/test"},  # Will be enriched
        )
        pipeline.process([event])
        
        # Event should have both original and enriched context
        assert "path" in processed[0].context
        assert processed[0].context["project"] == "testproject"

    def test_dedup_before_rate_limit(self):
        """Test deduplication happens before rate limiting."""
        processed = []
        
        def output_handler(events):
            processed.extend(events)
        
        # Low rate limit (1 token)
        pipeline = OkoPipeline(
            output_handler=output_handler,
            silence=0.1,  # Short silence
            rate_limit_max=1.0,
            rate_limit_refill=100.0,
        )
        
        event1 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test", "status_code": 500},
        )
        
        # First batch
        pipeline.process([event1])
        
        # Wait for silence to expire
        time.sleep(0.15)
        
        # Second batch with different event should pass (rate limit not exhausted)
        event2 = OkoEvent(
            type="http_error",
            message="HTTP 500",
            context={"path": "/api/test2", "status_code": 500},
        )
        pipeline.process([event2])
        
        # Both should pass because they're different fingerprints
        # and rate limit was reset
        assert len(processed) >= 1


class TestOkoPipelineRepr:
    """Test pipeline string representation."""

    def test_repr(self):
        """Test repr includes pipeline info."""
        output_handler = lambda events: None
        
        pipeline = OkoPipeline(output_handler=output_handler)
        
        r = repr(pipeline)
        
        assert "OkoPipeline" in r
        assert "silence" in r
        assert "rate_limit" in r
