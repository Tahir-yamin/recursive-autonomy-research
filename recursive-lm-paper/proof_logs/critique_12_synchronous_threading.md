# Proof of Resolution: Critique 12 (Synchronous Threading & Deadlocks)

## Original Critique
Synchronous Blocks: Blocking `requests.post` and `time.sleep()` destroy continuous batching. The entire engine stops, hanging concurrent users.
PagedAttention Deadlocks: Using `thread.join()` forces the scheduler to keep KV cache blocks locked in GPU memory while firing off a new context-heavy request, breaking the block allocator and causing OOMs.
Threading vs Async: Using OS threads defeats async generation. Must use native `asyncio`.

## Proof of Resolution
We replaced the synchronous `requests` library and OS-level threads with a fully async `aiohttp` non-blocking HTTP request architecture and native `asyncio` task scheduling.

### Code Snippet (`run_pilot_experiment.py`)
```python
import asyncio
import aiohttp

async def call_llm(prompt, system_prompt="..."):
    # ...
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=30) as response:
            if response.status == 200:
                res_data = await response.json()
                return res_data["choices"][0]["message"]["content"].strip()
            # ...
            await asyncio.sleep(1.0 * (2 ** attempt))

class AsyncMemoryConsolidator:
    def start_consolidation(self, compressed_history, raw_history_buffer):
        self.is_running = True
        self.task = asyncio.create_task(self._consolidate_worker(compressed_history, list(raw_history_buffer)))
```
All sequential loop training operations are wrapped via `asyncio.to_thread` to yield control cleanly to the asyncio event loop during PyTorch training blocks.
