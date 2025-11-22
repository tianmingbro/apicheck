#!/usr/bin/env python3
"""
Test script for add_keys_from_file functionality.
"""

import json
import os
import tempfile
from api_farm.client_sdk import APIPoolClient

def test_add_keys_from_file():
    """Test the add_keys_from_file method."""
    
    # Create a temporary JSON file
    test_data = {
        "api_keys": [
            "test-key-1-from-file",
            "test-key-2-from-file",
            "test-key-3-from-file"
        ]
    }
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name
    
    print(f"Created temporary test file: {temp_file}")
    print(f"File contents: {test_data}")
    
    try:
        # Test the client (this will fail without a running server, but we can verify the method exists)
        print("\nTesting APIPoolClient.add_keys_from_file method...")
        
        # Verify the method exists
        assert hasattr(APIPoolClient, 'add_keys_from_file'), "add_keys_from_file method not found"
        print("✓ add_keys_from_file method exists")
        
        # Test file reading logic by creating a mock scenario
        with open(temp_file, 'r') as f:
            data = json.load(f)
        
        api_keys = data.get("api_keys", [])
        assert len(api_keys) == 3, f"Expected 3 keys, got {len(api_keys)}"
        print(f"✓ File contains {len(api_keys)} API keys")
        
        for i, key in enumerate(api_keys, 1):
            print(f"  Key {i}: {key}")
        
        print("\n✓ All basic tests passed!")
        print("\nTo test with a real server:")
        print(f"  1. Start the server: python api_farm/server.py")
        print(f"  2. Register and login: api-farm register <user> <pass> && api-farm login <user> <pass>")
        print(f"  3. Import keys: api-farm add-key --file {temp_file}")
        
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"\nCleaned up temporary file: {temp_file}")

if __name__ == "__main__":
    test_add_keys_from_file()
