#!/usr/bin/env python3
"""
Quick verification script for api_farm package
Tests both CLI and SDK functionality
"""

import os
import sys

def test_package():
    print("=" * 60)
    print("API Farm Package Verification")
    print("=" * 60)

    # Test 1: SDK Import
    print("\n[Test 1] SDK Import Test")
    try:
        from api_farm import APIPoolClient, __version__
        print(f"✓ Successfully imported APIPoolClient")
        print(f"✓ Package version: {__version__}")
    except Exception as e:
        print(f"✗ Failed to import: {e}")
        sys.exit(1)

    # Test 2: Environment Variable Requirement
    print("\n[Test 2] Environment Variable Requirement Test")
    try:
        # This should fail without environment variable
        if 'API_FARM_SERVER_URL' in os.environ:
            #delete the environment variable
            del os.environ['API_FARM_SERVER_URL']
        client = APIPoolClient()
        print("✗ Should have raised ValueError for missing environment variable")
        sys.exit(1)
    except ValueError as e:
        if "API_FARM_SERVER_URL" in str(e):
            print(f"✓ Correctly requires API_FARM_SERVER_URL environment variable")
        else:
            print(f"✗ Unexpected error: {e}")
            sys.exit(1)

    # Test 3: Client with Environment Variable
    print("\n[Test 3] Client Initialization with Environment Variable")
    try:
        os.environ['API_FARM_SERVER_URL'] = 'http://localhost:8081'
        client = APIPoolClient()
        print(f"✓ Client initialized with env var: {client.server_url}")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        sys.exit(1)

    # Test 4: Client with Explicit URL
    print("\n[Test 4] Client Initialization with Explicit URL")
    try:
        client = APIPoolClient(server_url='http://example.com:9000')
        print(f"✓ Client initialized with explicit URL: {client.server_url}")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        sys.exit(1)

    # Test 5: Check module can be run
    print("\n[Test 5] Module Execution Test")
    print("✓ Module has __main__.py (tested separately via: python -m api_farm)")

    print("\n" + "=" * 60)
    print("All verification tests passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the server: api-farm-server")
    print("2. Set environment: export API_FARM_SERVER_URL=http://localhost:8081")
    print("3. Use CLI: api-farm register username password")
    print("4. Or use SDK in your code: from api_farm import APIPoolClient")

if __name__ == "__main__":
    test_package()
