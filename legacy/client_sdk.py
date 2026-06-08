# legacy/client_sdk.py
import json
import os
from typing import List, Dict, Any, Optional, Union
import httpx
from tqdm.asyncio import tqdm_asyncio
import asyncio          # 添加这一行

USE_CLIENT_DEFAULT = object()

class APIPoolClient:
    def __init__(self, server_url: Optional[str] = None, token: Optional[str] = None, timeout: float = 60.0):
        if server_url is None:
            server_url = os.getenv("KEYPILOT_SERVER_URL") or os.getenv("API_FARM_SERVER_URL")
        if not server_url:
            raise ValueError("Server URL must be provided or set in KEYPILOT_SERVER_URL environment variable.")
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.timeout = timeout

    # def _get_headers(self) -> Dict[str, str]:
    #     headers = {"Content-Type": "application/json"}
    #     if not self.token:
    #         raise RuntimeError("Not authenticated. Call login() first.")
    #     return {"Authorization": f"Bearer {self.token}"}
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, username: str, password: str) -> Dict[str, Any]:
        """Register a new user. Returns user info."""
        with httpx.Client(base_url=self.server_url, timeout=self.timeout) as client:
            resp = client.post("/auth/register", json={"username": username, "password": password})
            resp.raise_for_status()
            return resp.json()   # {id, username, role}

    def login(self, username: str, password: str) -> str:
        """Login and store token. Returns access_token."""
        with httpx.Client(base_url=self.server_url, timeout=self.timeout) as client:
            # OAuth2 密码流标准：application/x-www-form-urlencoded
            resp = client.post("/auth/login", data={"username": username, "password": password})
            resp.raise_for_status()
            data = resp.json()   # {access_token, token_type}
            self.token = data["access_token"]
            return self.token

    def logout(self) -> None:
        """Logout (client side only, server may not need)."""
        self.token = None

    def add_key(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1") -> Dict[str, Any]:
        """Add an API key. Returns created key info."""
        if not api_key:
            raise ValueError("API key cannot be empty or None")
        print('(self._get_headers())'+str(self._get_headers()))
        with httpx.Client(base_url=self.server_url, timeout=self.timeout) as client:
            resp = client.post("/keys", json={"key_value": api_key, "base_url": base_url},
                               headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()   # {id, key(脱敏), base_url, is_enabled, created_at, total_calls, last_used_at}

    def add_keys_from_file(self, file_path: str, base_url: str = "https://integrate.api.nvidia.com/v1") -> None:
        """Import multiple API keys from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        api_keys = data.get("api_keys", [])
        if not api_keys:
            raise ValueError("No API keys found in file. Expected 'api_keys' array.")
        for key in api_keys:
            self.add_key(key, base_url)
            print(f"✓ Added key: {key[:20]}...")

    def list_keys(self) -> List[Dict[str, Any]]:
        """List user's API keys (decrypted & masked)."""
        print('(self._get_headers())'+str(self._get_headers()))

        with httpx.Client(base_url=self.server_url, timeout=self.timeout) as client:
            resp = client.get("/keys", headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()   # list of APIKeyResponse objects

    def remove_key(self, key_id: int) -> None:
        """Remove an API key by its ID."""
        print('(self._get_headers())'+str(self._get_headers()))
        with httpx.Client(base_url=self.server_url, timeout=self.timeout) as client:
            resp = client.delete(f"/keys/{key_id}", headers=self._get_headers())
            resp.raise_for_status()

    async def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        stream: bool = False,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send a single chat completion request."""
        timeout = timeout or self.timeout
        async with httpx.AsyncClient(base_url=self.server_url, timeout=timeout) as client:
            print(f"Request URL: {self.server_url}/chat/completions")
            resp = await client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                    "stream": stream
                },
                headers=self._get_headers()
            )

            resp.raise_for_status()
            return resp.json()

    async def batch_chat_completions(
        self,
        batch_messages: List[List[Dict[str, str]]],
        model: str,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        concurrency: int = 8,
        timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Batch process multiple chat requests with concurrency control."""
        semaphore = asyncio.Semaphore(concurrency)
        results = [None] * len(batch_messages)

        async def process_one(idx: int, messages: List[Dict[str, str]]):
            async with semaphore:
                results[idx] = await self.chat_completions(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=False,
                    timeout=timeout
                )

        tasks = [asyncio.create_task(process_one(i, msgs)) for i, msgs in enumerate(batch_messages)]
        await tqdm_asyncio.gather(*tasks)
        return results