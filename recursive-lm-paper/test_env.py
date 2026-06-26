import os
import aiohttp
import asyncio

async def test():
    print("GEMINI_API_KEY present:", "GEMINI_API_KEY" in os.environ)
    print("OPENROUTER_API_KEY present:", "OPENROUTER_API_KEY" in os.environ)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": "Hello, write a 1 word reply"}]}],
            "generationConfig": {"temperature": 0.2}
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                    print("Status:", response.status)
                    print("Response:", await response.text())
            except Exception as e:
                print("Error:", e)
                
asyncio.run(test())
