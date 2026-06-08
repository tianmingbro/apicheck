from legacy.client_sdk import APIPoolClient
import asyncio
import logging
logging.basicConfig()
logging.getLogger("httpx").setLevel(logging.DEBUG)

def test():
    client = APIPoolClient(server_url="http://localhost:8000")
    print(f"Connecting to: {client.server_url}")

    # 1. 注册（可忽略重复注册错误）
    try:
        client.register("sdk_user1", "sdk_pass1")
    except Exception as e:
        if "already exists" not in str(e).lower():
            print(f"Registration failed: {e}")

    # 2. 登录
    token = client.login("sdk_user1", "sdk_pass1")
    print(f"Token: {token}")

    # 3. 添加 Key
    resp = client.add_key('sk-991aa8d5210f42fab50ce7f59dfca11a')
    key_id = resp.get("id")
    print(f"Added key with id: {key_id}")

    # 4. 调用聊天（需要确保路由正确）
    try:
        response = asyncio.run(client.chat_completions(
            model="qwen/qwen2.5-coder-7b-instruct",
            messages=[{"role": "user", "content": "Hello!"}]
        ))
        print("Response:", response)
    except Exception as e:
        print(f"Inference failed: {e}")

    # 5. 删除 Key
    print(client.remove_key(key_id))

    # 6. 登出
    client.logout()

    # （可选）登出后调用 list_keys 应该失败，但不要让它中断测试
    try:
        client.list_keys()
    except Exception as e:
        print(f"Expected error after logout: {e}")

if __name__ == "__main__":
    test()