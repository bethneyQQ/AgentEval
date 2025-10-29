"""
Trace Collector

Collects and batches trace events for efficient upload.
Implements async batching, retry mechanism, and local fallback.
"""

import asyncio
import time
import gzip
import json
import os
from typing import List, Dict, Any, Optional
from collections import deque
from pathlib import Path
import logging

from .trace_models import TraceEvent
from ..utils.http_client import AsyncHTTPClient

logger = logging.getLogger(__name__)


class TraceCollector:
    """Trace collector with async batching and retry"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)

        # Batch configuration
        batch_config = config.get('batch', {})
        self.max_batch_size = batch_config.get('max_size', 100)
        self.max_wait_seconds = batch_config.get('max_wait_seconds', 1.0)
        self.max_queue_size = batch_config.get('max_queue_size', 10000)

        # Queue
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.batch_buffer: List[TraceEvent] = []
        self.last_flush_time = time.time()

        # HTTP client
        endpoint = config.get('endpoint', 'http://localhost:8000')
        api_key = config.get('api_key', '')
        self.http_client = AsyncHTTPClient(
            base_url=endpoint,
            api_key=api_key,
            timeout=30
        )

        # Background task
        self.background_task: Optional[asyncio.Task] = None
        self._running = False

        # Local cache (for failures)
        self.local_cache_enabled = config.get('local_cache', {}).get('enabled', True)
        self.cache_dir = Path(config.get('local_cache', {}).get('cache_dir', '/tmp/agenteval_cache'))
        self.failed_batches: deque = deque(maxlen=1000)

        # Statistics
        self.stats = {
            'events_collected': 0,
            'events_uploaded': 0,
            'events_failed': 0,
            'batches_uploaded': 0,
            'batches_failed': 0
        }

    async def start(self):
        """Start the collector"""
        if not self.enabled:
            logger.info("TraceCollector is disabled")
            return

        logger.info("Starting TraceCollector...")
        self._running = True
        self.background_task = asyncio.create_task(self._batch_worker())

    async def stop(self):
        """Stop the collector"""
        if not self._running:
            return

        logger.info("Stopping TraceCollector...")
        self._running = False

        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

        # Flush remaining events
        await self._flush()
        await self.http_client.close()

        logger.info(f"TraceCollector stopped. Stats: {self.stats}")

    async def collect(self, event: TraceEvent):
        """Collect an event (non-blocking)"""
        if not self.enabled:
            return

        try:
            self.event_queue.put_nowait(event)
            self.stats['events_collected'] += 1
        except asyncio.QueueFull:
            logger.warning("Event queue is full, dropping event")
            self.stats['events_failed'] += 1

    async def _batch_worker(self):
        """Background worker for batching events"""
        logger.info("Batch worker started")

        while self._running:
            try:
                # Wait for event or timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.max_wait_seconds
                    )
                    self.batch_buffer.append(event)
                except asyncio.TimeoutError:
                    pass

                # Check if should flush
                should_flush = (
                    len(self.batch_buffer) >= self.max_batch_size or
                    (len(self.batch_buffer) > 0 and
                     time.time() - self.last_flush_time >= self.max_wait_seconds)
                )

                if should_flush:
                    await self._flush()

            except Exception as e:
                logger.error(f"Error in batch worker: {e}", exc_info=True)
                await asyncio.sleep(1)  # Back off on error

        logger.info("Batch worker stopped")

    async def _flush(self):
        """Flush batch buffer"""
        if not self.batch_buffer:
            return

        batch = self.batch_buffer[:]
        self.batch_buffer.clear()
        self.last_flush_time = time.time()

        logger.debug(f"Flushing {len(batch)} events...")

        # Process data
        processed_data = self._process_batch(batch)

        # Upload
        success = await self._upload(processed_data)

        if success:
            self.stats['events_uploaded'] += len(batch)
            self.stats['batches_uploaded'] += 1
        else:
            self.stats['events_failed'] += len(batch)
            self.stats['batches_failed'] += 1

            # Cache on failure
            if self.local_cache_enabled:
                self._cache_failed_batch(processed_data)

    def _process_batch(self, batch: List[TraceEvent]) -> Dict[str, Any]:
        """Process batch for upload"""
        # Convert to dicts
        traces = [event.to_dict() for event in batch]

        # Redact sensitive data (if configured)
        traces = self._redact_sensitive_data(traces)

        # Serialize
        data = json.dumps({'traces': traces})

        # Compress
        if self.config.get('performance', {}).get('use_compression', True):
            data = gzip.compress(data.encode('utf-8'))
            compressed = True
        else:
            data = data.encode('utf-8')
            compressed = False

        return {
            'data': data,
            'compressed': compressed,
            'count': len(traces)
        }

    def _redact_sensitive_data(self, traces: List[Dict]) -> List[Dict]:
        """Redact sensitive data from traces"""
        privacy_config = self.config.get('privacy', {})
        if not privacy_config.get('enabled', True):
            return traces

        import re
        sensitive_fields = [f.lower() for f in privacy_config.get('sensitive_fields', [])]
        patterns = privacy_config.get('redact_patterns', [])

        def redact_dict(d: Dict) -> Dict:
            result = {}
            for k, v in d.items():
                # Filter sensitive fields
                if k.lower() in sensitive_fields:
                    result[k] = "***REDACTED***"
                elif isinstance(v, dict):
                    result[k] = redact_dict(v)
                elif isinstance(v, list):
                    result[k] = [redact_dict(item) if isinstance(item, dict) else item for item in v]
                elif isinstance(v, str):
                    # Regex replacement
                    for pattern_config in patterns:
                        v = re.sub(
                            pattern_config['pattern'],
                            pattern_config['replacement'],
                            v
                        )
                    result[k] = v
                else:
                    result[k] = v
            return result

        return [redact_dict(trace) for trace in traces]

    async def _upload(self, data: Dict[str, Any]) -> bool:
        """Upload data with retry"""
        retry_config = self.config.get('retry', {})
        max_attempts = retry_config.get('max_attempts', 3)
        backoff_factor = retry_config.get('backoff_factor', 2.0)
        max_backoff = retry_config.get('max_backoff_seconds', 60)

        for attempt in range(max_attempts):
            try:
                response = await self.http_client.post(
                    '/api/v1/traces',
                    data=data['data'],
                    headers={
                        'Content-Encoding': 'gzip' if data['compressed'] else 'identity',
                        'Content-Type': 'application/json'
                    }
                )

                if response.status == 200:
                    logger.debug(f"Uploaded {data['count']} traces successfully")
                    return True
                else:
                    logger.warning(f"Upload failed with status {response.status}")

            except Exception as e:
                logger.error(f"Upload attempt {attempt + 1} failed: {e}")

            # Exponential backoff
            if attempt < max_attempts - 1:
                wait_time = min(backoff_factor ** attempt, max_backoff)
                await asyncio.sleep(wait_time)

        logger.error(f"Failed to upload after {max_attempts} attempts")
        return False

    def _cache_failed_batch(self, data: Dict[str, Any]):
        """Cache failed batch locally"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            filename = self.cache_dir / f"failed_{int(time.time() * 1000)}.json.gz"

            with open(filename, 'wb') as f:
                f.write(data['data'] if isinstance(data['data'], bytes) else data['data'].encode())

            self.failed_batches.append(str(filename))
            logger.info(f"Cached failed batch to {filename}")
        except Exception as e:
            logger.error(f"Failed to cache batch: {e}", exc_info=True)

    def get_stats(self) -> Dict[str, int]:
        """Get collector statistics"""
        return self.stats.copy()


# Global singleton
_trace_collector: Optional[TraceCollector] = None


def get_trace_collector(config: Optional[Dict] = None) -> TraceCollector:
    """Get TraceCollector singleton"""
    global _trace_collector
    if _trace_collector is None:
        if config is None:
            raise ValueError("TraceCollector not initialized. Provide config on first call.")
        _trace_collector = TraceCollector(config)
    return _trace_collector


def init_trace_collector(config: Dict[str, Any]) -> TraceCollector:
    """Initialize TraceCollector singleton"""
    global _trace_collector
    _trace_collector = TraceCollector(config)
    return _trace_collector
