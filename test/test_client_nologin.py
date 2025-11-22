from api_farm.client_sdk import APIPoolClient
import asyncio

def test():
    # Initialize client
    client = APIPoolClient(server_url="http://localhost:8081")


    # 4. Call LLM Generation (Inference)
    # This uses the shared pool of keys.
    print("Calling LLM...")
    try:
        response = asyncio.run(client.chat_completions(
            model="qwen/qwen2.5-coder-7b-instruct",
            messages=[{"role": "user", "content": "Hello!"}]
        ))
        print("Response:", response)
    except Exception as e:
        print(f"Inference failed (expected if key is dummy): {e}")

    # 5. Logout
    print("Logging out...")
    client.logout()

    # Verify Logout
    client.list_keys()
if __name__ == "__main__":
    test()

