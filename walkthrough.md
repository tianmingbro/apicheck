# API Pool Server Walkthrough

This walkthrough demonstrates how to use the API Pool Server, including the new features: **Logout** and **Persistence**.

## Prerequisites
Ensure the server is running:
```bash
python3 server.py
```

## CLI Usage

### 1. Register
Register a new user.
```bash
python3 cli.py register myuser mypass
```
*Output:* `Registered successfully. User ID: ...`

### 2. Login
Login to save your session token locally (`.auth_token`).
```bash
python3 cli.py login myuser mypass
```
*Output:* `Logged in successfully. Token saved.`

### 3. Add API Key
Add an OpenAI-compatible API key to your pool.
```bash
python3 cli.py add-key sk-my-api-key --base-url https://api.openai.com/v1
```
*Output:* `Key added successfully.`

### 4. List Keys
Verify your keys are stored.
```bash
python3 cli.py list-keys
```
*Output:*
```
Your Keys:
- sk-my-api-key
```

### 5. Logout
Invalidate your session and remove the local token.
```bash
python3 cli.py logout
```
*Output:* `Logged out successfully.`

### 6. Persistence Check
If you restart the server and login again, your keys will still be there.
```bash
# (Restart server)
python3 cli.py login myuser mypass
python3 cli.py list-keys
```

---

## Python SDK Usage

Here is a complete Python script demonstrating the flow.

```python
from client_sdk import APIPoolClient

# Initialize client
client = APIPoolClient(server_url="http://localhost:8081")

# 1. Register
print("Registering...")
user_id = client.register("sdk_user", "sdk_pass")
print(f"User ID: {user_id}")

# 2. Login
print("Logging in...")
token = client.login("sdk_user", "sdk_pass")
print(f"Token: {token}")

# 3. Add Key
print("Adding Key...")
client.add_key("sk-demo-key-123")

# 4. Call LLM Generation (Inference)
# This uses the shared pool of keys.
print("Calling LLM...")
try:
    response = client.chat_completions(
        model="qwen/qwen2.5-coder-7b-instruct",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print("Response:", response)
except Exception as e:
    print(f"Inference failed (expected if key is dummy): {e}")

# 5. Logout
print("Logging out...")
client.logout()

# Verify Logout
try:
    client.list_keys()
except RuntimeError as e:
    print(f"Caught expected error after logout: {e}")
```

## Verification Results
We ran `test_persistence_logout.py` which verified:
- [x] User registration and login.
- [x] Key addition.
- [x] Server restart (persistence).
- [x] Keys persist after restart.
- [x] Logout invalidates token on server.
