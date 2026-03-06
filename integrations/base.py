"""
Base Integration Classes
========================
Abstract base classes for all service integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
import aiohttp
import json


@dataclass
class IntegrationConfig:
    """Configuration for service integration."""
    name: str
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_delay: float = 1.0
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class BaseIntegration(ABC):
    """Base class for all service integrations."""

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            headers = {
                'Content-Type': 'application/json',
                **self.config.headers
            }
            if self.config.api_key:
                headers['Authorization'] = f'Bearer {self.config.api_key}'

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self._session

    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request with retry logic."""
        session = await self.get_session()
        url = f"{self.config.base_url}{endpoint}"

        for attempt in range(self.config.retry_count):
            try:
                async with session.request(
                    method,
                    url,
                    json=data,
                    params=params
                ) as response:
                    result = await response.json()

                    if response.status >= 400:
                        raise IntegrationError(
                            f"API error: {response.status}",
                            status=response.status,
                            response=result
                        )

                    return result

            except aiohttp.ClientError as e:
                if attempt == self.config.retry_count - 1:
                    raise IntegrationError(f"Request failed: {e}")
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        raise IntegrationError("Max retries exceeded")

    @abstractmethod
    async def sync(self, board) -> Dict:
        """Sync kanban board with service."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check service connectivity."""
        pass

    @abstractmethod
    def get_state_hash(self) -> str:
        """Get hash of current service state."""
        pass


class IntegrationError(Exception):
    """Error from service integration."""

    def __init__(self, message: str, status: int = None, response: Dict = None):
        super().__init__(message)
        self.status = status
        self.response = response


class WebhookHandler(ABC):
    """Base class for handling incoming webhooks."""

    @abstractmethod
    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        pass

    @abstractmethod
    async def process(self, event_type: str, payload: Dict) -> Dict:
        """Process webhook event."""
        pass


class SyncManager:
    """Manages synchronization between multiple services."""

    def __init__(self):
        self.integrations: Dict[str, BaseIntegration] = {}
        self.sync_locks: Dict[str, asyncio.Lock] = {}

    def register(self, name: str, integration: BaseIntegration):
        """Register an integration."""
        self.integrations[name] = integration
        self.sync_locks[name] = asyncio.Lock()

    async def sync_all(self, board) -> Dict[str, Dict]:
        """Sync board with all registered services."""
        results = {}
        tasks = []

        for name, integration in self.integrations.items():
            tasks.append(self._sync_with_lock(name, integration, board))

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for name, result in zip(self.integrations.keys(), completed):
            if isinstance(result, Exception):
                results[name] = {'success': False, 'error': str(result)}
            else:
                results[name] = result

        return results

    async def _sync_with_lock(
        self,
        name: str,
        integration: BaseIntegration,
        board
    ) -> Dict:
        """Sync with lock to prevent concurrent syncs."""
        async with self.sync_locks[name]:
            return await integration.sync(board)

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services."""
        results = {}

        tasks = [
            (name, integration.health_check())
            for name, integration in self.integrations.items()
        ]

        for name, task in tasks:
            try:
                results[name] = await task
            except Exception:
                results[name] = False

        return results
