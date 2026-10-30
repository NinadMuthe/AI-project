import asyncio
import selectors

def get_loop():
    return asyncio.SelectorEventLoop(selectors.SelectSelector())
