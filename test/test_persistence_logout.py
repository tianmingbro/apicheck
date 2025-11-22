import time
import subprocess
import sys
import os
import json
import requests
from api_farm.client_sdk import APIPoolClient

SERVER_URL = "http://localhost:8082"

def run_server():
    print("Starting server...")
    env = os.environ.copy()
    env["PORT"] = "8082"
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(2) # Wait for startup
    return process

def stop_server(process):
    print("Stopping server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def test_persistence_logout():
    # Clean up previous run
    if os.path.exists("users.json"): os.remove("users.json")
    if os.path.exists("keys.json"): os.remove("keys.json")
    if os.path.exists(".auth_token"): os.remove(".auth_token")

    # 1. Start Server
    server_proc = run_server()
    
    try:
        client = APIPoolClient(server_url=SERVER_URL)
        
        # 2. Register User
        print("Registering User A...")
        client.register("userA", "passA")
        
        # 3. Login
        print("Logging in User A...")
        token = client.login("userA", "passA")
        print(f"Token: {token}")
        
        # 4. Add Key
        print("Adding Key K1...")
        client.add_key("K1")
        
        # 5. Verify Key exists
        keys = client.list_keys()
        print(f"Keys: {keys}")
        assert "K1" in keys
        
        # 6. Stop Server
        stop_server(server_proc)
        print("Server stopped.")
        
        # 7. Restart Server (Persistence Check)
        server_proc = run_server()
        print("Server restarted.")
        
        # 8. Login again (New client instance to simulate fresh start, but using same credentials)
        client2 = APIPoolClient(server_url=SERVER_URL)
        client2.login("userA", "passA")
        
        # 9. Verify Key persists
        keys_after = client2.list_keys()
        print(f"Keys after restart: {keys_after}")
        assert "K1" in keys_after
        
        # 10. Logout
        print("Logging out...")
        token_to_logout = client2.token
        client2.logout()
        assert client2.token is None
        
        # 11. Verify token invalid on server
        print(f"Verifying token {token_to_logout} invalidation...")
        try:
            headers = {"Authorization": f"Bearer {token_to_logout}"}
            resp = requests.get(f"{SERVER_URL}/keys", headers=headers)
            if resp.status_code == 401:
                print("Token correctly invalidated (401).")
            else:
                print(f"Unexpected status code: {resp.status_code}")
                raise Exception("Token was not invalidated!")
        except Exception as e:
            print(f"Error checking token: {e}")
            raise

        # Let's verify client2 cannot list keys anymore using its internal token (which is None now)
        try:
            client2.list_keys()
            print("Error: Should have raised exception")
        except RuntimeError:
            print("Correctly raised RuntimeError for missing token.")

        print("Test finished successfully.")
        
    except Exception as e:
        print(f"Test FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if server_proc.poll() is None:
            stop_server(server_proc)

if __name__ == "__main__":
    test_persistence_logout()
