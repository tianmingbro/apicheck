from client_sdk import APIPoolClient

# Initialize client
client = APIPoolClient(server_url="http://localhost:8081")

# 1. Register
print("Registering...")
try:
    resp = client.register("sdk_user", "sdk_pass")
    print(f"Register Response 1: {resp['message']}, User ID: {resp['user_id']}")
    
    # Register again (should not fail)
    resp = client.register("sdk_user", "sdk_pass")
    print(f"Register Response 2: {resp['message']}, User ID: {resp['user_id']}")
    assert resp['message'] == "User already exists"
except Exception as e:
    print(f"Registration failed: {e}")

# 2. Login
print("Logging in...")
token = client.login("sdk_user", "sdk_pass")
print(f"Token: {token}")

# 3. Add Key
print("Adding Key...")
client.add_key("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")

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

# 4. Remove Key
print("Removing Key...")
print(client.remove_key("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"))

# 5. Logout
print("Logging out...")
client.logout()

# Verify Logout
try:
    client.list_keys()
except RuntimeError as e:
    print(f"Caught expected error after logout: {e}")