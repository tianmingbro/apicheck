import httpx
from typing import List, Dict, Any, Optional

class APIPoolClient:
    def __init__(self, server_url: str = "http://localhost:8081", token: Optional[str] = None):
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

    def chat_completions(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        top_p: float = 0.95,
        max_tokens: int = 1024,
        stream: bool = False
    ) -> Any:
        """
        Request a chat completion from the shared pool.
        No auth required for this endpoint.
        """
        with httpx.Client(base_url=self.server_url, timeout=60.0) as client:
            resp = client.post("/chat/completions", json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": stream
            })
            resp.raise_for_status()
            return resp.json()
