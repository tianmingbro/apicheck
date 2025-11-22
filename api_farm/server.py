import asyncio
import uuid
import secrets
import json
import os
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from openai import AsyncOpenAI
import itertools
import random

# --- Data Models ---

class UserRegisterRequest(BaseModel):
    username: str
    password: str

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserLoginResponse(BaseModel):
    token: str
    user_id: str

class AddKeyRequest(BaseModel):
    api_key: str
    base_url: str = "https://integrate.api.nvidia.com/v1"

class RemoveKeyRequest(BaseModel):
    api_key: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = 1.0
    top_p: float = 0.95
    max_tokens: int = 1024
    stream: bool = False

# --- Core Logic ---

class UserManager:
    def __init__(self):
        # username -> {password, user_id}
        self.users: Dict[str, Dict[str, str]] = {}
        # token -> user_id
        self.tokens: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self.load_users()

    def load_users(self):
        if os.path.exists("users.json"):
            try:
                with open("users.json", "r") as f:
                    self.users = json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")

    def save_users(self):
        try:
            with open("users.json", "w") as f:
                json.dump(self.users, f)
        except Exception as e:
            print(f"Error saving users: {e}")

    async def register(self, username, password) -> tuple[str, bool]:
        async with self._lock:
            if username in self.users:
                # Return existing user_id and False (not new)
                return self.users[username]["user_id"], False
            
            user_id = str(uuid.uuid4())
            self.users[username] = {"password": password, "user_id": user_id}
            self.save_users()
            return user_id, True

    async def login(self, username, password) -> str:
        async with self._lock:
            user = self.users.get(username)
            if not user or user["password"] != password:
                raise ValueError("Invalid credentials")
            
            # Generate simple token
            token = secrets.token_hex(16)
            self.tokens[token] = user["user_id"]
            return token, user["user_id"]

    async def get_user_id_by_token(self, token: str) -> Optional[str]:
        async with self._lock:
            return self.tokens.get(token)

    async def logout(self, token: str):
        async with self._lock:
            if token in self.tokens:
                del self.tokens[token]
                return "Logout successful"
            else:
                return "Logout failed: Not logged in"

class KeyPool:
    def __init__(self):
        # Map user_id -> List[api_key]
        self.user_keys: Dict[str, List[str]] = {}
        # Map api_key -> AsyncOpenAI client
        self.clients: Dict[str, AsyncOpenAI] = {}
        # List of all available api_keys for rotation
        self.all_keys: List[str] = []
        self._lock = asyncio.Lock()
        self.load_keys()

    def load_keys(self):
        if os.path.exists("keys.json"):
            try:
                with open("keys.json", "r") as f:
                    data = json.load(f)
                    self.user_keys = data.get("user_keys", {})
                    # Reconstruct clients
                    for uid, keys in self.user_keys.items():
                        for key in keys:
                            if key not in self.clients:
                                self.clients[key] = AsyncOpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
                                self.all_keys.append(key)
            except Exception as e:
                print(f"Error loading keys: {e}")

    def save_keys(self):
        try:
            with open("keys.json", "w") as f:
                json.dump({"user_keys": self.user_keys}, f)
        except Exception as e:
            print(f"Error saving keys: {e}")

    async def ensure_user_init(self, user_id: str):
        async with self._lock:
            if user_id not in self.user_keys:
                self.user_keys[user_id] = []

    async def add_key(self, user_id: str, api_key: str, base_url: str):
        async with self._lock:
            if user_id not in self.user_keys:
                self.user_keys[user_id] = []
            
            if api_key in self.clients:
                # Key already exists globally, just associate with user if not already
                if api_key not in self.user_keys[user_id]:
                    self.user_keys[user_id].append(api_key)
                return

            # Create new client
            client = AsyncOpenAI(base_url=base_url, api_key=api_key)
            self.clients[api_key] = client
            self.user_keys[user_id].append(api_key)
            self.all_keys.append(api_key)
            self.save_keys()

    async def remove_key(self, user_id: str, api_key: str):
        async with self._lock:
            if user_id not in self.user_keys:
                return "User has no keys" # User has no keys
            
            if api_key in self.user_keys[user_id]:
                self.user_keys[user_id].remove(api_key)
                msg = "Key removed successfully"
            else:
                # raise ValueError("Key not found for this user")
                return "Key not found for this user"
            
            # Check if this key is used by any other user
            is_used = False
            for uid, keys in self.user_keys.items():
                if api_key in keys:
                    is_used = True
                    break
            
            if not is_used:
                # Remove from global pool
                if api_key in self.clients:
                    del self.clients[api_key]
                if api_key in self.all_keys:
                    self.all_keys.remove(api_key)
            else:
                raise ValueError("Key should not be used by any other user")
            
            self.save_keys()
            return msg

    async def get_user_keys(self, user_id: str) -> List[str]:
        async with self._lock:
            return list(self.user_keys.get(user_id, []))

    async def get_all_clients_snapshot(self) -> List[AsyncOpenAI]:
        """Return a snapshot list of clients for rotation attempts."""
        async with self._lock:
            if not self.all_keys:
                return []
            # Return a shuffled list to avoid thundering herd on the same key order
            keys = list(self.all_keys)
            random.shuffle(keys)
            return [self.clients[k] for k in keys]

user_manager = UserManager()
pool = KeyPool()
security = HTTPBearer()

# --- Dependencies ---

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = await user_manager.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id

# --- API ---

app = FastAPI()

@app.post("/users/register")
async def register_user(req: UserRegisterRequest):
    try:
        user_id, is_new = await user_manager.register(req.username, req.password)
        # Initialize empty key list for user
        await pool.ensure_user_init(user_id)
        
        if is_new:
            return {"user_id": user_id, "message": "User registered successfully"}
        else:
            return {"user_id": None, "message": "User already exists"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/users/login", response_model=UserLoginResponse)
async def login_user(req: UserLoginRequest):
    try:
        token, user_id = await user_manager.login(req.username, req.password)
        return UserLoginResponse(token=token, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/users/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    await user_manager.logout(token)
    return {"message": "Logged out successfully"}

@app.post("/keys")
async def add_key(req: AddKeyRequest, user_id: str = Depends(get_current_user_id)):
    await pool.add_key(user_id, req.api_key, req.base_url)
    return {"status": "ok", "message": "Key added"}

@app.get("/keys")
async def list_keys(user_id: str = Depends(get_current_user_id)):
    keys = await pool.get_user_keys(user_id)
    return {"keys": keys}

@app.delete("/keys")
async def remove_key(req: RemoveKeyRequest, user_id: str = Depends(get_current_user_id)):
    try:
        msg = await pool.remove_key(user_id, req.api_key)
        return {"status": "ok", "message": msg}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    Public endpoint. Uses shared pool.
    """
    clients = await pool.get_all_clients_snapshot()
    if not clients:
        raise HTTPException(status_code=503, detail="No API keys available in the pool")

    last_error = None
    
    for client in clients:
        try:
            response = await client.chat.completions.create(
                model=req.model,
                messages=req.messages,
                temperature=req.temperature,
                top_p=req.top_p,
                max_tokens=req.max_tokens,
                stream=req.stream
            )
            return response
        except Exception as e:
            last_error = e
            print(f"Client failed: {e}. Retrying with next key...")
            continue
    
    raise HTTPException(status_code=502, detail=f"All API keys failed. Last error: {str(last_error)}")

def get_local_ip():
    """Get the local IP address of this machine."""
    import socket
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external server (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"

def main():
    """Main entry point for the server CLI."""
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description="API Farm Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to (default: 8081)")
    args = parser.parse_args()
    
    # Get local IP for display
    local_ip = get_local_ip()

    ''' 
    print("=" * 60)
    print("API Farm Server Starting...")
    print("=" * 60)
    print(f"Server running on:")
    print(f"  - Local:   http://localhost:{args.port}")
    print(f"  - Network: http://{local_ip}:{args.port}")
    print()
    print("To connect clients, set the environment variable:")
    print(f"  export API_FARM_SERVER_URL=http://{local_ip}:{args.port}")
    print()
    print("Or if connecting from the same machine:")
    print(f"  export API_FARM_SERVER_URL=http://localhost:{args.port}")
    print("=" * 60)
    print()'''
    
    # ANSI Colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"

    print(f"{CYAN}{'=' * 60}{RESET}")
    print(f"{GREEN}API Farm Server Starting...{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}")

    print(f"{YELLOW}Server running on:{RESET}")
    print(f"  - Local:   {BLUE}http://localhost:{args.port}{RESET}")
    print(f"  - Network: {BLUE}http://{local_ip}:{args.port}{RESET}")
    print()

    print(f"{YELLOW}To connect clients, set the environment variable:{RESET}")
    print(f"  export API_FARM_SERVER_URL={GREEN}http://{local_ip}:{args.port}{RESET}")
    print()

    print(f"{YELLOW}Or if connecting from the same machine:{RESET}")
    print(f"  export API_FARM_SERVER_URL={GREEN}http://localhost:{args.port}{RESET}")
    print(f"{CYAN}{'=' * 60}{RESET}\n")

    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
