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
    Handles retries with exponential backoff, configurable timeouts, and structured error reporting.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or getattr(settings, "ML_SERVICE_URL", "http://localhost:9000")).rstrip("/")
        self.timeout = float(timeout or getattr(settings, "ML_SERVICE_TIMEOUT", 30))
        self.api_key = api_key or getattr(settings, "ML_SERVICE_API_KEY", "")

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Internal-Token"] = self.api_key
        return headers

    async def check_health(self) -> Dict[str, Any]:
        """
        Probes the ml-service /health endpoint.
        Returns health status dict or raises Exception if unreachable.
        """
        url = f"{self.base_url}/health"
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"ML Service returned status {resp.status_code}",
            )

    async def predict_async(
        self,
        subject: str,
        body: str,
        threshold: Optional[float] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Sends an asynchronous prediction request to ml-service with automatic retries.
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
                async with httpx.AsyncClient(timeout=self.timeout) as client:
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
                with httpx.Client(timeout=self.timeout) as client:
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
            except Exception as err:
                last_error = str(err)
                logger.error(f"[Sync Attempt {attempt}/{max_retries}] Unexpected error: {err}")

            if attempt < max_retries:
                time.sleep(0.5 * (2 ** (attempt - 1)))

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML Service unavailable after {max_retries} attempts: {last_error}",
        )
