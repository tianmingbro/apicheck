# API Farm

A shared API key pool server and client for managing and using API keys efficiently. This package supports both command-line interface (CLI) and programmatic (SDK) usage.

## Features

- **Shared API Key Pool**: Centralize API keys for multiple users
- **User Management**: Register, login, and manage API keys per user
- **Dual Interface**: Use via CLI commands or Python SDK
- **Load Balancing**: Automatic rotation across available API keys
- **Easy Installation**: Pip-installable package

## Installation

### From Source (Development)
```bash
# Clone the repository
git clone <your-repo-url>
cd api_farm

# Install in development mode
pip install -e .
```

### From PyPI (When Published)
```bash
pip install api-farm
```

## Quick Start

### 1. Start the Server

```bash
# Start the server (prints IP address for client connection)
api-farm-server

# Or with custom host/port
api-farm-server --host 0.0.0.0 --port 8081
```

The server will display connection information:
```
============================================================
API Farm Server Starting...
============================================================
Server running on:
  - Local:   http://localhost:8081
  - Network: http://192.168.1.100:8081

To connect clients, set the environment variable:
  export API_FARM_SERVER_URL=http://192.168.1.100:8081
============================================================
```

### 2. Configure Client Environment

**Required:** Set the server URL as an environment variable:

```bash
# Use the URL displayed by the server
export API_FARM_SERVER_URL=http://localhost:8081
```

### 3. Use the CLI

```bash
# Register a new user
api-farm register myuser mypassword

# Login
api-farm login myuser mypassword

# Add an API key
api-farm add-key "your-api-key-here"

# List your keys
api-farm list-keys

# Remove a key
api-farm remove-key "your-api-key-here"

# Logout
api-farm logout
```

## Usage

### Command Line Interface (CLI)

The CLI requires the `API_FARM_SERVER_URL` environment variable to be set.

**Available Commands:**
- `python -m api_farm register <username> <password>` - Register a new user
- `python -m api_farm login <username> <password>` - Login and save authentication token
- `python -m api_farm logout` - Logout and remove token
- `python -m api_farm add-key <api_key> [--base-url <url>]` - Add an API key to your pool
- `python -m api_farm list-keys` - List all your API keys
- `python -m api_farm remove-key <api_key>` - Remove an API key from your pool
- `python -m api_farm chat "[{\"role\":\"user\", \"content\":\"Hello!\"}]"` and it succeeded.
- `python -m api_farm batch-chat -f batch_messages.json` with a test file and it succeeded.


**Server Commands:**
- `api-farm-server [--host HOST] [--port PORT]` - Start the API Farm server

### Python SDK

Import and use the client in your Python code:

```python
from api_farm import APIPoolClient
import os

# Method 1: Use environment variable
os.environ['API_FARM_SERVER_URL'] = 'http://localhost:8081'
client = APIPoolClient()

# Method 2: Pass server URL explicitly
client = APIPoolClient(server_url='http://localhost:8081')

# Register a user
response = client.register('username', 'password')
print(response)

# Login
token = client.login('username', 'password')

# Add API key
client.add_key('your-api-key', base_url='https://integrate.api.nvidia.com/v1')

# List keys
keys = client.list_keys()
print(keys)

# Make a chat completion request (uses shared pool)
response = client.chat_completions(
    model='meta/llama-3.1-8b-instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=100
)
print(response)

# Remove a key
client.remove_key('your-api-key')

# Logout
client.logout()
```

### Programmatic Server Usage

You can also start the server programmatically:

```python
from api_farm.server import app
import uvicorn

# Start the server
uvicorn.run(app, host="0.0.0.0", port=8081)
```

## Environment Variables

- **`API_FARM_SERVER_URL`** (Required for clients): The URL of the API Farm server
  - Example: `http://localhost:8081`
  - Set before using CLI or SDK

## Architecture

- **Server** (`api_farm.server`): FastAPI-based server managing users and API keys
- **Client SDK** (`api_farm.client_sdk`): Python client for programmatic access
- **CLI** (`api_farm.cli`): Command-line interface for interactive use

## Development

### Running Tests
```bash
python -m pytest test/
```

### Building the Package
```bash
# Install build tools
pip install build

# Build distribution packages
python -m build

# Install from wheel
pip install dist/api_farm-*.whl
```

## License

MIT License
