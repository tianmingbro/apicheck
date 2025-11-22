import httpx
import os
import json
from typing import List, Dict, Any, Optional

class APIPoolClient:
    def __init__(self, server_url: Optional[str] = None, token: Optional[str] = None):
        # Try to get server URL from environment variable if not provided
        if server_url is None:
            server_url = os.getenv('API_FARM_SERVER_URL')
        
        if not server_url:
            raise ValueError(
                "Server URL must be provided either via the 'server_url' parameter or "
                "by setting the 'API_FARM_SERVER_URL' environment variable.\n"
                "Example: export API_FARM_SERVER_URL=http://localhost:8081"
            )
        
        self.server_url = server_url
        self.token = token
        self.user_id: Optional[str] = None

    def register(self, username, password) -> str:
        """Register a new user."""
        with httpx.Client(base_url=self.server_url) as client:
            resp = client.post("/users/register", json={"username": username, "password": password})
            resp.raise_for_status()
            print(resp.json()["message"])
            return resp.json()

    def login(self, username, password) -> str:
        """Login and store token."""
        with httpx.Client(base_url=self.server_url) as client:
            resp = client.post("/users/login", json={"username": username, "password": password})
            resp.raise_for_status()
            data = resp.json()
            self.token = data["token"]
            self.user_id = data["user_id"]
            return self.token

    def logout(self):
        """Logout and invalidate token."""
        if self.token:
            with httpx.Client(base_url=self.server_url) as client:
                msg = client.post("/users/logout", headers=self._get_headers())
            self.token = None
            self.user_id = None
            print(msg.json()["message"])
        else:
            print("Not logged in. Call login() first.")

    def _get_headers(self):
        if not self.token:
            raise RuntimeError("Not authenticated. Call login() first.")

        return {"Authorization": f"Bearer {self.token}"}

    def add_key(self, api_key: str, base_url: str = "https://integrate.api.nvidia.com/v1"):
        """Add an API key to the user's pool."""
        with httpx.Client(base_url=self.server_url) as client:
            resp = client.post("/keys", json={
                "api_key": api_key,
                "base_url": base_url
            }, headers=self._get_headers())
            resp.raise_for_status()

    def add_keys_from_file(self, file_path: str, base_url: str = "https://integrate.api.nvidia.com/v1"):
        """Import multiple API keys from a JSON file.
        
        Args:
            file_path: Path to JSON file containing API keys
            base_url: Base URL for the API service (default: NVIDIA API)
            
        The JSON file should follow this format:
        {
            "api_keys": ["key1", "key2", "key3"]
        }
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file: {e}")
        
        api_keys = data.get("api_keys", [])
        if not api_keys:
            raise ValueError("No API keys found in file. Expected 'api_keys' array.")
        
        if not isinstance(api_keys, list):
            raise ValueError("'api_keys' must be an array in the JSON file.")
        
        success_count = 0
        failed_keys = []
        
        for key in api_keys:
            try:
                self.add_key(key, base_url)
                success_count += 1
                print(f"✓ Added key: {key[:20]}...")
            except Exception as e:
                failed_keys.append((key, str(e)))
                print(f"✗ Failed to add key {key[:20]}...: {e}")
        
        print(f"\nImport complete: {success_count}/{len(api_keys)} keys added successfully.")
        if failed_keys:
            print(f"{len(failed_keys)} keys failed to import.")


    def list_keys(self) -> Optional[List[str]]:
        """List user's keys."""
        if not self.token:
            print("Not logged in. Call login() first.")
            return None
        with httpx.Client(base_url=self.server_url) as client:
            resp = client.get("/keys", headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()["keys"]

    def remove_key(self, api_key: str):
        """Remove an API key from the user's pool."""
        with httpx.Client(base_url=self.server_url) as client:
            resp = client.request("DELETE", "/keys", json={
                "api_key": api_key
            }, headers=self._get_headers())
            print(resp.text)
            resp.raise_for_status()


    async def chat_completions(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Any:
        """
        Request a single chat completion.
        
        Args:
            messages: List of message objects
            model: Model name to use
            temperature: Temperature parameter
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses
            
        Returns:
            Response dictionary
        """
        import asyncio
        
        async with httpx.AsyncClient(base_url=self.server_url, timeout=60.0) as client:
            resp = await client.post("/chat/completions", json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": stream
            })
            resp.raise_for_status()
            return resp.json()

    async def batch_chat_completions(
        self,
        batch_messages: List[List[Dict[str, Any]]],
        model: str,
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        stream: bool = False,
        concurrency: int = 8
    ) -> List[Any]:
        """
        Request multiple chat completions from the shared pool in batch.
        Results are returned in the same order as the input messages.
        No auth required for this endpoint.
        
        Args:
            batch_messages: List of message arrays, each representing one chat request
            model: Model name to use
            temperature: Temperature parameter
            top_p: Top-p sampling parameter
            max_tokens: Maximum tokens to generate
            stream: Whether to stream responses (not supported in batch mode)
            concurrency: Maximum number of concurrent requests (default: 8)
            
        Returns:
            List of response dictionaries in the same order as input
        """
        import asyncio
        
        sem = asyncio.Semaphore(concurrency)
        results: List[Any] = [None] * len(batch_messages)
        
        async def _process_one(idx: int, messages: List[Dict[str, Any]]) -> None:
            async with sem:
                async with httpx.AsyncClient(base_url=self.server_url, timeout=60.0) as client:
                    resp = await client.post("/chat/completions", json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "top_p": top_p,
                        "max_tokens": max_tokens,
                        "stream": stream
                    })
                    resp.raise_for_status()
                    results[idx] = resp.json()
        
        tasks = [
            asyncio.create_task(_process_one(i, msgs)) 
            for i, msgs in enumerate(batch_messages)
        ]
        await asyncio.gather(*tasks)
        
        return results
