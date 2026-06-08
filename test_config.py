#!/usr/bin/env python
# quick_test.py - 验证 APIPoolClient 与服务端的兼容性

import sys
import os

# 可选：手动指定服务端地址（若不设置环境变量）
# os.environ["KEYPILOT_SERVER_URL"] = "http://localhost:8000"

from legacy.client_sdk import APIPoolClient

def main():
    # 设置服务端地址（优先从环境变量读取，否则用默认）
    server_url = os.getenv("KEYPILOT_SERVER_URL", "http://localhost:8000")
    print(f"连接服务端: {server_url}")
    
    client = APIPoolClient(server_url=server_url)
    username = "testuser_quick"
    password = "quickpass123"
    
    # 1. 注册用户
    try:
        print("\n1. 注册用户...")
        user_info = client.register(username, password)
        print(f"   ✅ 注册成功: {user_info}")
    except Exception as e:
        if "Username already registered" in str(e):
            print(f"   ⚠️ 用户已存在，继续登录...")
        else:
            print(f"   ❌ 注册失败: {e}")
            return

    # 2. 登录
    try:
        print("\n2. 登录...")
        token = client.login(username, password)
        print(f"   ✅ 登录成功，Token: {token[:30]}...")
    except Exception as e:
        print(f"   ❌ 登录失败: {e}")
        return

    # 3. 添加一个测试 API Key
    try:
        print("\n3. 添加测试 API Key...")
        test_key = "sk-test1234567890abcdef"
        key_info = client.add_key(test_key, base_url=None)  # 让服务端使用默认 upstream
        print(f"   ✅ Key 添加成功: {key_info}")
    except Exception as e:
        print(f"   ❌ 添加 Key 失败: {e}")

    # 4. 列出已有 Key
    try:
        print("\n4. 列出所有 API Key...")
        keys = client.list_keys()
        if keys:
            for k in keys:
                print(f"   - ID: {k['id']}, Key: {k['key']}, Enabled: {k['is_enabled']}")
        else:
            print("   ⚠️ 当前无 API Key")
    except Exception as e:
        print(f"   ❌ 列出 Key 失败: {e}")

    # 5. 测试聊天接口（需要有效上游 Key，这里仅验证请求格式）
    try:
        print("\n5. 尝试发送简单聊天请求（需要上游 Key 有效）...")
        # 使用一个最小的请求，实际是否成功取决于 upstream Key 是否有效
        response = client.chat_completions(
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            model="gpt-3.5-turbo",   # 或更换为你上游支持的模型
            max_tokens=10
        )
        print(f"   ✅ 聊天响应: {response.get('choices', [{}])[0].get('message', {}).get('content', '')[:50]}")
    except Exception as e:
        print(f"   ⚠️ 聊天请求失败（可能上游 Key 无效或配额不足）: {e}")

    print("\n✅ 基础功能验证完成。")

if __name__ == "__main__":
    main()