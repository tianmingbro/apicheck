from client_sdk import APIPoolClient
import sys

def reproduce():
    client = APIPoolClient(server_url="http://localhost:8081")
    try:
        print("Attempting to list keys without login...")
        keys = client.list_keys()
        print(f"Keys: {keys}")
    except Exception as e:
        print(f"Caught expected exception: {e}")

if __name__ == "__main__":
    reproduce()
