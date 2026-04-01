import uvicorn
import os
import sys
import asyncio

if __name__ == "__main__":
    # On Windows, selector loop is usually quieter than proactor for local dev
    # and avoids noisy transient accept errors like WinError 64 in some cases.
    if sys.platform.startswith("win"):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    reload_enabled = os.getenv("BIORESEARCHER_RELOAD", "false").lower() in ("1", "true", "yes")
    uvicorn.run(app="app.main:app", host="127.0.0.1", port=8000, reload=reload_enabled)
