import time
import subprocess
import sys
import os
import json
import asyncio
from api_farm.client_sdk import APIPoolClient

def test_system():
    # 1. Start Server
    print("Starting server...")
    server_process = subprocess.Popen(
        [sys.executable, "api_farm/server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(5)
    
    try:
        # 2. Initialize Clients
        client1 = APIPoolClient(server_url="http://localhost:8081")
        client2 = APIPoolClient(server_url="http://localhost:8081")
        
        # 3. Register Users
        print("Registering users...")
        client1.register("user1", "pass1")
        client2.register("user2", "pass2")
        
        # 4. Login
        print("Logging in...")
        client1.login("user1", "pass1")
        client2.login("user2", "pass2")
        
        # 5. Add Keys
        api_keys = []
        try:
            with open("api.json", "r") as f:
                data = json.load(f)
                api_keys = data.get("api_keys", [])
        except FileNotFoundError:
            print("Warning: api.json not found. Using dummy keys.")
            api_keys = ["dummy-key-1", "dummy-key-2"]

        if not api_keys:
             api_keys = ["dummy-key-1", "dummy-key-2"]

        print(f"Adding key for User 1: {api_keys[0]}")
        client1.add_key(api_keys[0])
        
        if len(api_keys) > 1:
            print(f"Adding key for User 2: {api_keys[1]}")
            client2.add_key(api_keys[1])
            
        # 6. List Keys
        print("Listing keys...")
        keys1 = client1.list_keys()
        print(f"User 1 keys: {keys1}")
        assert api_keys[0] in keys1
        
        # 7. Test Inference (Public endpoint, uses shared pool)
        print("Testing inference...")
        try:
            resp = asyncio.run(client2.chat_completions(
                model="qwen/qwen2-7b-instruct",
                messages=[{"role": "user", "content": "Hello"}]
            ))
            print("Inference success:", resp)
        except Exception as e:
            print(f"Inference failed (expected if keys are dummy): {e}")
        
        # 8. Remove Key
        print("Removing key for User 1...")
        client1.remove_key(api_keys[0])
        
        # 9. Verify Removal
        keys1_after = client1.list_keys()
        print(f"User 1 keys after removal: {keys1_after}")
        assert api_keys[0] not in keys1_after

        print("Test finished successfully.")

    finally:
        print("Stopping server...")
        server_process.terminate()
        server_process.wait()
        stdout, stderr = server_process.communicate()
        print("Server STDOUT:", stdout)
        print("Server STDERR:", stderr)

if __name__ == "__main__":
    test_system()
