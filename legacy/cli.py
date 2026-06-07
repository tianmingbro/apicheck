# legacy/cli.py
import argparse
import sys
import os
import json
import asyncio
from dotenv import load_dotenv
from .client_sdk import APIPoolClient

load_dotenv()

SERVER_URL = os.getenv("KEYPILOT_SERVER_URL", "http://localhost:8000")
TOKEN_FILE = ".auth_token"

def save_token(token: str):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token() -> str | None:
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

def remove_token():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def main():
    # 环境变量检查（可选，因为有默认值）
    if not os.getenv('KEYPILOT_SERVER_URL'):
        print("Warning: KEYPILOT_SERVER_URL not set, using default http://localhost:8000")

    parser = argparse.ArgumentParser(description="KeyPilot CLI - API Key Pool Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- register ---
    p = subparsers.add_parser("register", help="Register a new user")
    p.add_argument("username")
    p.add_argument("password")

    # --- login ---
    p = subparsers.add_parser("login", help="Login and save token")
    p.add_argument("username")
    p.add_argument("password")

    # --- logout ---
    subparsers.add_parser("logout", help="Logout (remove local token)")

    # --- add-key ---
    p = subparsers.add_parser("add-key", help="Add an API key")
    p.add_argument("key", nargs="?", help="API key value")
    p.add_argument("--base-url", default="https://integrate.api.nvidia.com/v1")
    p.add_argument("--file", "-f", help="Import keys from JSON file (requires 'api_keys' array)")

    # --- list-keys ---
    subparsers.add_parser("list-keys", help="List all API keys (masked)")

    # --- remove-key ---
    p = subparsers.add_parser("remove-key", help="Remove an API key by its ID")
    p.add_argument("key_id", type=int, help="ID of the key to remove")

    # --- chat ---
    p = subparsers.add_parser("chat", help="Send a chat completion")
    p.add_argument("message", nargs="?", help="User message")
    p.add_argument("--file", "-f", help="JSON file with messages array")
    p.add_argument("--model", "-m", default="meta/llama-3.1-8b-instruct")
    p.add_argument("--temperature", "-t", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--system", help="System message")

    # --- batch-chat ---
    p = subparsers.add_parser("batch-chat", help="Batch chat from JSON file")
    p.add_argument("--file", "-f", required=True, help="JSON file containing array of message arrays")
    p.add_argument("--model", "-m", default="meta/llama-3.1-8b-instruct")
    p.add_argument("--temperature", "-t", type=float, default=1.0)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--concurrency", "-c", type=int, default=8)
    p.add_argument("--output", "-o", choices=["json", "text"], default="text")

    args = parser.parse_args()

    token = load_token()
    client = APIPoolClient(server_url=SERVER_URL, token=token)

    try:
        if args.command == "register":
            resp = client.register(args.username, args.password)
            print(f"✅ User registered. ID: {resp['id']}, Username: {resp['username']}")

        elif args.command == "login":
            if token:
                print("Already logged in. Use 'logout' first.")
                sys.exit(1)
            token = client.login(args.username, args.password)
            save_token(token)
            print("✅ Logged in successfully.")

        elif args.command == "logout":
            if not token:
                print("Not logged in.")
                sys.exit(1)
            client.logout()
            remove_token()
            print("✅ Logged out.")

        elif args.command == "add-key":
            if not args.key and not args.file:
                print("Error: Provide a key or use --file.")
                sys.exit(1)
            if args.key and args.file:
                print("Error: Cannot use both key and --file.")
                sys.exit(1)
            if args.file:
                client.add_keys_from_file(args.file, args.base_url)
            else:
                result = client.add_key(args.key, args.base_url)
                print(f"✅ Key added. ID: {result['id']}, Key: {result['key']}")

        elif args.command == "list-keys":
            keys = client.list_keys()
            if not keys:
                print("No API keys found.")
            else:
                print("Your API keys:")
                for k in keys:
                    print(f"  ID: {k['id']}, Key: {k['key']}, Enabled: {k['is_enabled']}, Calls: {k['total_calls']}")

        elif args.command == "remove-key":
            client.remove_key(args.key_id)
            print(f"✅ Key ID {args.key_id} removed.")

        elif args.command == "chat":
            if not args.message and not args.file:
                print("Error: Provide a message or --file.")
                sys.exit(1)
            if args.message and args.file:
                print("Error: Cannot use both message and --file.")
                sys.exit(1)

            if args.file:
                with open(args.file, 'r') as f:
                    messages = json.load(f)
                if not isinstance(messages, list):
                    print("Error: JSON file must contain an array of messages.")
                    sys.exit(1)
            else:
                messages = []
                if args.system:
                    messages.append({"role": "system", "content": args.system})
                messages.append({"role": "user", "content": args.message})

            response = asyncio.run(client.chat_completions(
                messages=messages,
                model=args.model,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens
            ))
            # 标准 OpenAI 响应格式
            if 'choices' in response:
                content = response['choices'][0]['message']['content']
                print(content)
                if 'usage' in response:
                    print(f"\n[Tokens: {response['usage']['total_tokens']}]")
            else:
                print(json.dumps(response, indent=2))

        elif args.command == "batch-chat":
            with open(args.file, 'r') as f:
                batch_messages = json.load(f)
            if not isinstance(batch_messages, list):
                print("Error: JSON file must contain an array of message arrays.")
                sys.exit(1)

            print(f"Processing {len(batch_messages)} requests (concurrency={args.concurrency})...")
            responses = asyncio.run(client.batch_chat_completions(
                batch_messages=batch_messages,
                model=args.model,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens,
                concurrency=args.concurrency
            ))
            if args.output == "json":
                print(json.dumps(responses, indent=2))
            else:
                for i, resp in enumerate(responses, 1):
                    print(f"\n[{i}/{len(responses)}]")
                    if 'choices' in resp:
                        print(resp['choices'][0]['message']['content'])
                    else:
                        print(json.dumps(resp))
                print(f"\n✅ Batch completed.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()