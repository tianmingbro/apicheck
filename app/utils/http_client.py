"""HTTP client utilities with proxy support for China deployments.

httpx respects the standard HTTP_PROXY / HTTPS_PROXY environment variables
automatically.  This module provides a thin factory with additional safeguards.

Usage:
    from app.utils.http_client import create_http_client
    with create_http_client(timeout=120) as client:
        resp = client.post(url, json=payload, headers=headers)
"""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_http_client(timeout: float = 120.0) -> httpx.Client:
    """Create a synchronous httpx Client with proxy awareness.

    Proxy precedence:
    1. Explicit HTTPS_PROXY / HTTP_PROXY environment variables (httpx reads them natively)
    2. The settings.HTTPS_PROXY value (applied via env override)

    On Alibaba Cloud / servers inside China, set HTTPS_PROXY to a proxy that
    can reach api.openai.com (e.g. Clash, V2Ray, or a corporate proxy).
    """
    # If settings has an explicit proxy, help httpx by setting it in the env
    # (httpx already reads these, but being explicit helps debugging)
    client_kwargs = {"timeout": timeout}

    proxy_url = settings.HTTPS_PROXY or settings.HTTP_PROXY
    if proxy_url:
        logger.debug("Using proxy: %s", proxy_url.split("@")[-1] if "@" in proxy_url else proxy_url)
        client_kwargs["proxy"] = proxy_url

    return httpx.Client(**client_kwargs)


def check_upstream_connectivity(test_url: str = "https://api.openai.com/v1/models") -> dict:
    """Quick connectivity check to upstream API.

    Returns a dict with keys: ok (bool), latency_ms (int), error (str|None).
    Call this from a health-check endpoint or startup probe.
    """
    import time
    result = {"ok": False, "latency_ms": 0, "error": None}
    try:
        start = time.time()
        with create_http_client(timeout=10.0) as client:
            resp = client.get(test_url)
            result["latency_ms"] = int((time.time() - start) * 1000)
            result["ok"] = 200 <= resp.status_code < 300
            if not result["ok"]:
                result["error"] = f"Upstream returned {resp.status_code}"
    except httpx.TimeoutException:
        result["error"] = "Connection timed out — check network/proxy"
    except Exception as e:
        result["error"] = str(e)

    return result
