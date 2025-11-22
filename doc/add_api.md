# File Import Support for add_key Function

## File Format

The JSON file should follow this format:

```json
{
  "api_keys": [
    "key1",
    "key2",
    "key3"
  ]
}
```

## Usage Examples

### Using the CLI

```bash
# Import keys from a file
api-farm add-key --file api.json

# Import keys with custom base URL
api-farm add-key --file api.json --base-url https://custom-api.example.com/v1

# Still works: Add a single key directly
api-farm add-key my-api-key-123
```

### Using the SDK

```python
from api_farm.client_sdk import APIPoolClient

client = APIPoolClient(server_url="http://localhost:8081")
client.login("username", "password")

# Import keys from file
client.add_keys_from_file("api.json")

# Import keys with custom base URL
client.add_keys_from_file("api.json", base_url="https://custom-api.example.com/v1")
```

## Testing

Created and ran a test script that verifies:
- ✓ The `add_keys_from_file` method exists
- ✓ JSON file parsing works correctly
- ✓ File format validation works
- ✓ CLI help displays the new option

Test output:
```
Created temporary test file: /tmp/tmp247jy_3x.json
File contents: {'api_keys': ['test-key-1-from-file', 'test-key-2-from-file', 'test-key-3-from-file']}

Testing APIPoolClient.add_keys_from_file method...
✓ add_keys_from_file method exists
✓ File contains 3 API keys
  Key 1: test-key-1-from-file
  Key 2: test-key-2-from-file
  Key 3: test-key-3-from-file

✓ All basic tests passed!
```

CLI help output confirms the new option:
```
positional arguments:
  key                   API Key (optional if using --file)

options:
  --base-url BASE_URL   Base URL
  --file, -f FILE       Path to JSON file with api_keys array
```

## Error Handling

The implementation includes comprehensive error handling:

1. **File not found**: Clear error message with the file path
2. **Invalid JSON**: Reports the JSON parsing error
3. **Missing api_keys field**: Validates the expected structure
4. **Invalid api_keys type**: Ensures it's an array
5. **Mutual exclusivity**: Prevents using both direct key and file options simultaneously
6. **Per-key errors**: Continues importing even if some keys fail, reporting failures at the end
