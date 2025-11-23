#!/usr/bin/env python3
"""
Stress test for the API server.
Sends a large number of concurrent requests to verify server stability.
"""

import asyncio
import pytest
from api_farm.client_sdk import APIPoolClient

@pytest.mark.asyncio
async def test_stress_api():
    """
    Stress test the API with a large number of concurrent requests.
    """
    # Configuration
    NUM_REQUESTS = 10000
    CONCURRENCY = 200
    SERVER_URL = "http://localhost:8081"
    
    print(f"\nStarting stress test with {NUM_REQUESTS} requests (concurrency: {CONCURRENCY})...")
    
    # Initialize client
    client = APIPoolClient(server_url=SERVER_URL)
    
    # Prepare batch messages
    # We'll use a simple question to avoid token limits or complex processing
    base_message = [{"role": "user", "content": "What is 1+1? Answer briefly."}]
    batch_messages = [base_message for _ in range(NUM_REQUESTS)]
    
    try:
        # Make batch request
        responses = await client.batch_chat_completions(
            batch_messages=batch_messages,
            model="meta/llama-3.1-8b-instruct",
            temperature=0.7,
            max_tokens=5000,
            concurrency=CONCURRENCY,
            timeout=600000.0  # Increased timeout for stress test
        )
        
        # Verify results
        success_count = 0
        errors = []
        
        for i, response in enumerate(responses):
            if isinstance(response, dict) and 'choices' in response:
                success_count += 1
            else:
                errors.append(f"Request {i} failed: {response}")
        
        print(f"Completed {len(responses)} requests.")
        print(f"Success rate: {success_count}/{NUM_REQUESTS} ({success_count/NUM_REQUESTS*100:.1f}%)")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors[:10]:  # Show first 10 errors
                print(error)
            if len(errors) > 10:
                print(f"...and {len(errors)-10} more errors.")
        
        # Assertions
        assert len(responses) == NUM_REQUESTS, f"Expected {NUM_REQUESTS} responses, got {len(responses)}"
        assert success_count == NUM_REQUESTS, f"Only {success_count}/{NUM_REQUESTS} requests succeeded"
        
    except Exception as e:
        pytest.fail(f"Stress test failed with exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_stress_api())
