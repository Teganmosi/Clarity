import httpx
import asyncio
import time
import os
from collections import deque
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class RateLimiter:
    def __init__(self, rate_limit: int):
        self.rate_limit = rate_limit
        self.calls = deque()

    async def acquire(self):
        now = time.time()
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        if len(self.calls) >= self.rate_limit:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        self.calls.append(time.time())


class BaseAPIClient:
    def __init__(self, base_url: str, api_key: str, rate_limit: int = 100):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limiter = RateLimiter(rate_limit)
        self.client = httpx.AsyncClient(timeout=30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        await self.rate_limiter.acquire()
        try:
            response = await self.client.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Request failed: {str(e)}")
            return None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Clarity-Sales-Platform/1.0"
        }

    async def close(self):
        await self.client.aclose()
