"""
Async HTTP Client

Provides async HTTP client for trace data upload.
"""

import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available, HTTP client will be disabled")


class AsyncHTTPClient:
    """Async HTTP client for trace upload"""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[Any] = None

    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is not installed. Install with: pip install aiohttp")

        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def post(
        self,
        path: str,
        data: Any,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Send POST request"""
        await self._ensure_session()

        url = f"{self.base_url}{path}"
        headers = headers or {}

        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        headers.setdefault('Content-Type', 'application/json')

        try:
            async with self.session.post(url, data=data, headers=headers) as response:
                return response
        except Exception as e:
            logger.error(f"HTTP POST failed: {e}")
            raise

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
