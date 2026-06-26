import os
import aiohttp
import asyncio

async def test():
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    print("ANTHROPIC_API_KEY present:", bool(anthropic_key))
    if not anthropic_key:
        return
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": anthropic_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "messages": [
            {"role": "user", "content": "Hello, write a 1 word reply"}
        ],
        "max_tokens": 10,
        "temperature": 0.2
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                print("Status:", response.status)
                print("Response:", await response.text())
        except Exception as e:
            print("Error:", e)
                
asyncio.run(test())
