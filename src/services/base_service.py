# src/services/base_service.py
from abc import ABC, abstractmethod
from typing import Any, Optional
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class BaseService(ABC):
    """Abstract base class for external services"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None

    @abstractmethod
    async def initialize(self):
        """Initialize the service client"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if service is healthy"""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(self, operation: str, **kwargs) -> Any:
        """Make request with retry logic"""
        try:
            return await self._execute_operation(operation, **kwargs)
        except Exception as e:
            raise ServiceError(f"Service operation failed: {e}")

    @abstractmethod
    async def _execute_operation(self, operation: str, **kwargs) -> Any:
        """Execute specific service operation"""
        pass