#!/usr/bin/env python3
"""
Test script for batch chat completions.
Demonstrates both CLI and programmatic usage of async batch processing.
"""

import asyncio
import json
from api_farm.client_sdk import APIPoolClient

async def test_batch_chat():
    """Test batch chat completions programmatically."""
    
    # Initialize client
    client = APIPoolClient()
    
    # Prepare batch messages
    batch_messages = [
        [{"role": "user", "content": "What is 2+2?"}],
        [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a short joke about programming."}
        ],
        [{"role": "user", "content": "What is the capital of France?"}]
    ]
    
    print(f"Testing batch chat with {len(batch_messages)} requests...")
    print(f"Concurrency: 8")
    print("=" * 60)
    
    # Make batch request
    responses = await client.batch_chat_completions(
        batch_messages=batch_messages,
        model="meta/llama-3.1-8b-instruct",
        temperature=1.0,
        top_p=0.95,
        max_tokens=1024,
        concurrency=8
    )
    
    # Display results
    for i, response in enumerate(responses, 1):
        print(f"\n[Request {i}]")
        if isinstance(response, dict) and 'choices' in response:
            content = response['choices'][0]['message']['content']
            print(content)
            if 'usage' in response:
                print(f"[Tokens: {response['usage']['total_tokens']}]")
        print("-" * 60)
    
    print(f"\n✓ Successfully processed {len(responses)} requests")
    return responses

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_batch_chat())
