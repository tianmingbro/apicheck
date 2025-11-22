import argparse
import sys
import os
import json
import asyncio
from api_farm.client_sdk import APIPoolClient

TOKEN_FILE = ".auth_token"

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

def remove_token():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

def main():
    # Check if environment variable is set
    if not os.getenv('API_FARM_SERVER_URL'):
        print("Error: API_FARM_SERVER_URL environment variable is not set.")
        print("Please set it before running the CLI:")
        print("  export API_FARM_SERVER_URL=http://localhost:8081")
        print("\nOr get the server URL by running: api-farm-server")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="API Pool CLI")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register
    register_parser = subparsers.add_parser("register", help="Register a new user")
    register_parser.add_argument("username", help="Username")
    register_parser.add_argument("password", help="Password")
    
    # Login
    login_parser = subparsers.add_parser("login", help="Login and save token")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")
    
    # Logout
    subparsers.add_parser("logout", help="Logout")
    
    # Add Key
    add_key_parser = subparsers.add_parser("add-key", help="Add an API key")
    add_key_parser.add_argument("key", nargs="?", help="API Key (optional if using --file)")
    add_key_parser.add_argument("--base-url", default="https://integrate.api.nvidia.com/v1", help="Base URL")
    add_key_parser.add_argument("--file", "-f", help="Path to JSON file with api_keys array")
    
    # List Keys
    subparsers.add_parser("list-keys", help="List your API keys")
    
    # Remove Key
    remove_key_parser = subparsers.add_parser("remove-key", help="Remove an API key")
    remove_key_parser.add_argument("key", help="API Key")
    
    # Chat Completion
    chat_parser = subparsers.add_parser("chat", help="Send a chat completion request")
    chat_parser.add_argument("message", nargs="?", help="User message to send")
    chat_parser.add_argument("--file", "-f", help="Path to JSON file with messages array")
    chat_parser.add_argument("--model", "-m", default="meta/llama-3.1-8b-instruct", help="Model name")
    chat_parser.add_argument("--temperature", "-t", type=float, default=1.0, help="Temperature (default: 1.0)")
    chat_parser.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling (default: 0.95)")
    chat_parser.add_argument("--max-tokens", type=int, default=1024, help="Maximum tokens (default: 1024)")
    chat_parser.add_argument("--system", help="System message")
    
    # Batch Chat Completion
    batch_chat_parser = subparsers.add_parser("batch-chat", help="Send multiple chat completion requests in batch")
    batch_chat_parser.add_argument("--file", "-f", required=True, help="Path to JSON file with array of message arrays")
    batch_chat_parser.add_argument("--model", "-m", default="meta/llama-3.1-8b-instruct", help="Model name")
    batch_chat_parser.add_argument("--temperature", "-t", type=float, default=1.0, help="Temperature (default: 1.0)")
    batch_chat_parser.add_argument("--top-p", type=float, default=0.95, help="Top-p sampling (default: 0.95)")
    batch_chat_parser.add_argument("--max-tokens", type=int, default=1024, help="Maximum tokens (default: 1024)")
    batch_chat_parser.add_argument("--concurrency", "-c", type=int, default=8, help="Max concurrent requests (default: 8)")
    batch_chat_parser.add_argument("--output", "-o", choices=["json", "text"], default="text", help="Output format (default: text)")
    
    
    args = parser.parse_args()
    
    token = load_token()
    # Client will use environment variable for server_url
    client = APIPoolClient(token=token)
    
    try:
        if args.command == "register":
            resp = client.register(args.username, args.password)
            print(f"{resp['message']} User ID: {resp['user_id']}")
            
        elif args.command == "login":
            if token:
                print("Already logged in. Please logout first.")
                sys.exit(1)
            token = client.login(args.username, args.password)
            save_token(token)
            print("Logged in successfully. Token saved.")
            
        elif args.command == "logout":
            if not token:
                print("Not logged in.")
                sys.exit(1)
            client.logout()
            remove_token()
            print("Logged out successfully.")
            
        elif args.command == "add-key":
            # Validate input
            if not args.key and not args.file:
                print("Error: Either provide a key or use --file to specify a JSON file with keys.")
                sys.exit(1)
            
            if args.key and args.file:
                print("Error: Cannot use both key argument and --file option.")
                sys.exit(1)
            
            if args.file:
                # Import from file
                client.add_keys_from_file(args.file, args.base_url)
            else:
                # Add single key
                client.add_key(args.key, args.base_url)
                print("Key added successfully.")
            
        elif args.command == "list-keys":
            keys = client.list_keys()
            if keys is None:
                print("Warning: You are not logged in.")
            else:
                print("Your Keys:")
                for k in keys:
                    print(f"- {k}")
                
        elif args.command == "remove-key":
            client.remove_key(args.key)
            print("Key removed successfully.")
        
        elif args.command == "chat":
            # Validate input
            if not args.message and not args.file:
                print("Error: Either provide a message or use --file to specify a messages file.")
                sys.exit(1)
            
            if args.message and args.file:
                print("Error: Cannot use both message argument and --file option.")
                sys.exit(1)
            
            # Construct messages array
            messages = []
            
            if args.file:
                # Read from file
                try:
                    with open(args.file, 'r') as f:
                        messages = json.load(f)
                    if not isinstance(messages, list):
                        print("Error: JSON file must contain an array of message objects.")
                        sys.exit(1)
                except FileNotFoundError:
                    print(f"Error: File not found: {args.file}")
                    sys.exit(1)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in file: {e}")
                    sys.exit(1)
            else:
                # Build from arguments
                if args.system:
                    messages.append({"role": "system", "content": args.system})
                messages.append({"role": "user", "content": args.message})
            
            # Make the request
            try:
                response = asyncio.run(client.chat_completions(
                    model=args.model,
                    messages=messages,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    stream=False
                ))
                
                # Extract and display response
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    print(content)
                    
                    # Show usage info if available
                    if hasattr(response, 'usage'):
                        print(f"\n[Model: {args.model}, Tokens: {response.usage.total_tokens}]")
                elif isinstance(response, dict) and 'choices' in response:
                    content = response['choices'][0]['message']['content']
                    print(content)
                    
                    # Show usage info if available
                    if 'usage' in response:
                        print(f"\n[Model: {args.model}, Tokens: {response['usage']['total_tokens']}]")
                else:
                    print("Response:", response)
            except Exception as chat_error:
                print(f"Chat completion error: {chat_error}")
                sys.exit(1)
        
        elif args.command == "batch-chat":
            # Read batch messages from file
            try:
                with open(args.file, 'r') as f:
                    batch_messages = json.load(f)
                
                if not isinstance(batch_messages, list):
                    print("Error: JSON file must contain an array of message arrays.")
                    sys.exit(1)
                
                # Validate that each item is a list of messages
                for i, msgs in enumerate(batch_messages):
                    if not isinstance(msgs, list):
                        print(f"Error: Item {i} is not a message array.")
                        sys.exit(1)
                        
            except FileNotFoundError:
                print(f"Error: File not found: {args.file}")
                sys.exit(1)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in file: {e}")
                sys.exit(1)
            
            # Make the batch request
            try:
                print(f"Processing {len(batch_messages)} requests with concurrency={args.concurrency}...")
                
                responses = asyncio.run(client.batch_chat_completions(
                    batch_messages=batch_messages,
                    model=args.model,
                    temperature=args.temperature,
                    top_p=args.top_p,
                    max_tokens=args.max_tokens,
                    stream=False,
                    concurrency=args.concurrency
                ))
                
                # Display results
                if args.output == "json":
                    # Output as JSON
                    print(json.dumps(responses, indent=2))
                else:
                    # Output as numbered text
                    print(f"\n{'='*60}")
                    print(f"Batch Results ({len(responses)} responses)")
                    print(f"{'='*60}\n")
                    
                    for i, response in enumerate(responses, 1):
                        print(f"[{i}/{len(responses)}]")
                        
                        if isinstance(response, dict) and 'choices' in response:
                            content = response['choices'][0]['message']['content']
                            print(content)
                            
                            # Show usage info if available
                            if 'usage' in response:
                                print(f"\n[Tokens: {response['usage']['total_tokens']}]")
                        else:
                            print("Response:", response)
                        
                        if i < len(responses):
                            print(f"\n{'-'*60}\n")
                    
                    print(f"\n{'='*60}")
                    print(f"Completed {len(responses)} requests")
                    print(f"{'='*60}")
                    
            except Exception as batch_error:
                print(f"Batch chat completion error: {batch_error}")
                sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
