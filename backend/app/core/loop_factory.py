import asyncio
import selectors

# On Windows, the default event loop (ProactorEventLoop) is incompatible with async
# PostgreSQL drivers like psycopg. We enforce the SelectorEventLoop globally.
if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def get_loop():
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


