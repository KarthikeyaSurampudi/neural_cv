# Async utilities

import asyncio


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.create_task(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)