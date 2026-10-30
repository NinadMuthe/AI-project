import sys
import os

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        app_dir="backend",
        loop="app.core.loop_factory:get_loop",
    )
