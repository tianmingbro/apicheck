import argparse
import sys
import os
import json
from client_sdk import APIPoolClient

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
    parser = argparse.ArgumentParser(description="API Pool CLI")
    parser.add_argument("--server", default="http://localhost:8081", help="Server URL")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Register
    register_parser = subparsers.add_parser("register", help="Register a new user")
    register_parser.add_argument("username", help="Username")
    register_parser.add_argument("password", help="Password")
    
    # Login
    login_parser = subparsers.add_parser("login", help="Login and save token")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")
    
    # Logout
    subparsers.add_parser("logout", help="Logout")
    
    # Add Key
    add_key_parser = subparsers.add_parser("add-key", help="Add an API key")
    add_key_parser.add_argument("key", help="API Key")
    add_key_parser.add_argument("--base-url", default="https://integrate.api.nvidia.com/v1", help="Base URL")
    
    # List Keys
    subparsers.add_parser("list-keys", help="List your API keys")
    
    # Remove Key
    remove_key_parser = subparsers.add_parser("remove-key", help="Remove an API key")
    remove_key_parser.add_argument("key", help="API Key")
    
    args = parser.parse_args()
    
    token = load_token()
    client = APIPoolClient(server_url=args.server, token=token)
    
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
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
