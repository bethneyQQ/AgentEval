"""
Unit tests for Trace Collector
"""

import pytest
import asyncio
import time
from agenteval_plugin.trace import TraceCollector, TraceEvent, init_trace_collector


@pytest.fixture
def collector_config():
    """Test configuration for collector"""
    return {
        'enabled': True,
        'endpoint': 'http://localhost:8000',
        'api_key': 'test_key',
        'batch': {
            'max_size': 5,  # Small batch for testing
            'max_wait_seconds': 0.5,
            'max_queue_size': 100,
        },
        'retry': {
            'max_attempts': 2,
            'backoff_factor': 1.0,
            'max_backoff_seconds': 5,
        },
        'privacy': {
            'enabled': True,
            'sensitive_fields': ['password', 'token'],
            'redact_patterns': [],
        },
        'performance': {
            'use_compression': False,  # Disable for testing
        },
        'local_cache': {
            'enabled': True,
            'cache_dir': '/tmp/test_agenteval_cache',
        }
    }


@pytest.fixture
def trace_event():
    """Create test trace event"""
    return TraceEvent(
        trace_id="trace_123",
        span_id="span_456",
        parent_span_id=None,
        name="test.event",
        start_time=time.time(),
        end_time=time.time() + 1.0,
        attributes={'test': 'value'},
        events=[],
        status='ok'
    )


class TestTraceCollector:
    """Test trace collector functionality"""

    @pytest.mark.asyncio
    async def test_collector_init(self, collector_config):
        """Test collector initialization"""
        collector = TraceCollector(collector_config)
        assert collector.enabled is True
        assert collector.max_batch_size == 5

    @pytest.mark.asyncio
    async def test_collector_start_stop(self, collector_config):
        """Test collector can start and stop"""
        collector = TraceCollector(collector_config)
        await collector.start()
        assert collector._running is True

        await collector.stop()
        assert collector._running is False

    @pytest.mark.asyncio
    async def test_event_collection(self, collector_config, trace_event):
        """Test events can be collected"""
        collector = TraceCollector(collector_config)
        await collector.start()

        await collector.collect(trace_event)
        assert collector.stats['events_collected'] == 1

        await collector.stop()

    @pytest.mark.asyncio
    async def test_batch_flushing(self, collector_config, trace_event):
        """Test batch flushing based on size"""
        collector = TraceCollector(collector_config)
        await collector.start()

        # Collect multiple events to trigger batch flush
        for i in range(6):  # More than max_batch_size
            event = TraceEvent(
                trace_id=f"trace_{i}",
                span_id=f"span_{i}",
                parent_span_id=None,
                name="test.event",
                start_time=time.time(),
                end_time=None,
                attributes={},
                events=[],
                status='ok'
            )
            await collector.collect(event)

        # Wait for batch processing
        await asyncio.sleep(1.0)

        assert collector.stats['events_collected'] == 6

        await collector.stop()

    @pytest.mark.asyncio
    async def test_sensitive_data_redaction(self, collector_config):
        """Test sensitive data is redacted"""
        collector = TraceCollector(collector_config)

        traces = [
            {
                'attributes': {
                    'password': 'secret123',
                    'username': 'test_user'
                }
            }
        ]

        redacted = collector._redact_sensitive_data(traces)
        assert redacted[0]['attributes']['password'] == '***REDACTED***'
        assert redacted[0]['attributes']['username'] == 'test_user'

    def test_batch_processing(self, collector_config, trace_event):
        """Test batch data processing"""
        collector = TraceCollector(collector_config)

        batch = [trace_event] * 3
        processed = collector._process_batch(batch)

        assert processed['count'] == 3
        assert 'data' in processed
        assert processed['compressed'] is False

    @pytest.mark.asyncio
    async def test_collector_stats(self, collector_config, trace_event):
        """Test collector statistics"""
        collector = TraceCollector(collector_config)
        await collector.start()

        await collector.collect(trace_event)
        await collector.collect(trace_event)

        stats = collector.get_stats()
        assert stats['events_collected'] == 2

        await collector.stop()

    @pytest.mark.asyncio
    async def test_disabled_collector(self, collector_config, trace_event):
        """Test disabled collector doesn't collect"""
        collector_config['enabled'] = False
        collector = TraceCollector(collector_config)

        await collector.start()
        await collector.collect(trace_event)

        # Should not collect when disabled
        assert collector.stats['events_collected'] == 0

    @pytest.mark.asyncio
    async def test_queue_overflow(self, collector_config):
        """Test behavior when queue is full"""
        collector_config['batch']['max_queue_size'] = 2
        collector = TraceCollector(collector_config)
        await collector.start()

        # Try to add more events than queue can hold
        for i in range(5):
            event = TraceEvent(
                trace_id=f"trace_{i}",
                span_id=f"span_{i}",
                parent_span_id=None,
                name="test",
                start_time=time.time(),
                end_time=None,
                attributes={},
                events=[],
                status='ok'
            )
            await collector.collect(event)

        # Some events should be dropped
        assert collector.stats['events_failed'] > 0

        await collector.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
