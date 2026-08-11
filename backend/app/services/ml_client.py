import asyncio
import logging
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("mailsentry.ml_client")


class MLServiceClient:
    """
    Asynchronous and synchronous HTTP client for communicating with the independent ml-service microservice.
    Handles retries with exponential backoff, configurable timeouts, connection pooling, and structured error reporting.
    """

    _sync_client: Optional[httpx.Client] = None
    _async_client: Optional[httpx.AsyncClient] = None

    @classmethod
    def _get_sync_client(cls, timeout: float) -> httpx.Client:
        if cls._sync_client is None or cls._sync_client.is_closed:
            cls._sync_client = httpx.Client(
                timeout=timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0),
            )
        return cls._sync_client

    @classmethod
    def _get_async_client(cls, timeout: float) -> httpx.AsyncClient:
        if cls._async_client is None or cls._async_client.is_closed:
            cls._async_client = httpx.AsyncClient(
                timeout=timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=50, keepalive_expiry=30.0),
            )
        return cls._async_client

    @classmethod
    async def close_async_client(cls):
        if cls._async_client is not None and not cls._async_client.is_closed:
            await cls._async_client.aclose()
            cls._async_client = None

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
    ):
        raw_url = base_url or getattr(settings, "ML_SERVICE_URL", "http://127.0.0.1:9000")
        self.base_url = raw_url.rstrip("/")
        self.timeout = float(timeout or getattr(settings, "ML_SERVICE_TIMEOUT", 120.0))
        self.api_key = api_key or getattr(settings, "ML_SERVICE_API_KEY", "")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Internal-Token"] = self.api_key
        return headers

    async def check_health(self) -> Dict[str, Any]:
        """
        Probes the ml-service /health endpoint with IPv4/localhost fallback.
        Returns health status dict or raises Exception if unreachable.
        """
        urls = [self.base_url]
        if "127.0.0.1" in self.base_url:
            urls.append(self.base_url.replace("127.0.0.1", "localhost"))
        elif "localhost" in self.base_url:
            urls.append(self.base_url.replace("localhost", "127.0.0.1"))

        last_err = None
        for base in urls:
            url = f"{base}/health"
            try:
                client = self._get_async_client(10.0)
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
            except Exception as err:
                last_err = err

        if last_err:
            raise last_err
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Service health check failed.",
        )

    async def predict_async(
        self,
        subject: str,
        body: str,
        threshold: Optional[float] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Sends an asynchronous prediction request to ml-service using persistent HTTP connection pooling.
        """
        url = f"{self.base_url}/predict"
        payload = {
            "subject": subject or "",
            "body": body or "",
            "threshold": threshold,
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                client = self._get_async_client(self.timeout)
                resp = await client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                
                err_msg = f"ML Service returned HTTP {resp.status_code}: {resp.text}"
                logger.warning(f"[Attempt {attempt}/{max_retries}] {err_msg}")
                last_error = err_msg

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = str(net_err)
                logger.warning(
                    f"[Attempt {attempt}/{max_retries}] Connection failed to ML Service at {url}: {net_err}"
                )
                await self.close_async_client()
            except Exception as err:
                last_error = str(err)
                logger.error(f"[Attempt {attempt}/{max_retries}] Unexpected error in MLServiceClient: {err}")

            if attempt < max_retries:
                backoff_sec = 0.5 * (2 ** (attempt - 1))
                await asyncio.sleep(backoff_sec)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML Service unavailable after {max_retries} attempts: {last_error}",
        )

    def predict_sync(
        self,
        subject: str,
        body: str,
        threshold: Optional[float] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:

        """
        Synchronous prediction helper for worker threads or synchronous routes.
        Uses persistent HTTP connection pooling to prevent socket exhaustion during bulk email classification.
        """
        url = f"{self.base_url}/predict"
        payload = {
            "subject": subject or "",
            "body": body or "",
            "threshold": threshold,
        }

        client = self._get_sync_client(self.timeout)
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = client.post(url, json=payload, headers=self._get_headers())
                if resp.status_code == 200:
                    return resp.json()
                
                err_msg = f"ML Service returned HTTP {resp.status_code}: {resp.text}"
                logger.warning(f"[Sync Attempt {attempt}/{max_retries}] {err_msg}")
                last_error = err_msg

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as net_err:
                last_error = str(net_err)
                logger.warning(
                    f"[Sync Attempt {attempt}/{max_retries}] Connection failed to ML Service at {url}: {net_err}"
                )
                # Reset cached connection pool on socket error
                try:
                    client.close()
                except Exception:
                    pass
                MLServiceClient._sync_client = None
                client = self._get_sync_client(self.timeout)
            except Exception as err:
                last_error = str(err)
                logger.error(f"[Sync Attempt {attempt}/{max_retries}] Unexpected error: {err}")

            if attempt < max_retries:
                time.sleep(0.5 * (2 ** (attempt - 1)))

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML Service unavailable after {max_retries} attempts: {last_error}",
        )

