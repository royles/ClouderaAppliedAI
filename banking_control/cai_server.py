"""Start Uvicorn from CDSW/CAI notebook kernels (already running an asyncio loop)."""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Any


def _notebook_kernel_active() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        pass
    try:
        from IPython import get_ipython  # type: ignore[import-not-found]

        if get_ipython() is not None:
            return True
    except ImportError:
        pass
    return bool(os.environ.get("CDSW_PROJECT"))


def _run_uvicorn_isolated(
    app: Any,
    *,
    host: str,
    port: int,
) -> None:
    """Run Uvicorn on a fresh asyncio loop (never the Jupyter kernel loop)."""
    import uvicorn

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        reload=False,
        log_level=os.environ.get("BANKING_CONTROL_LOG_LEVEL", "info"),
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    try:
        loop.run_until_complete(server.serve())
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


def serve_fastapi_app(
    app: Any,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    reload: bool = False,
) -> None:
    """
    Run Uvicorn for ``app``.

    CDSW/CAI Applications execute inside IPython, which already owns an asyncio
    event loop. ``uvicorn.run()`` / ``asyncio.run()`` cannot be used on that
    loop, so we start an isolated server loop on a worker thread instead.
    """
    if reload:
        raise ValueError("reload=True is not supported for Banking Control on CDSW/CAI")

    if not _notebook_kernel_active():
        _run_uvicorn_isolated(app, host=host, port=port)
        return

    errors: list[BaseException] = []

    def _serve() -> None:
        try:
            _run_uvicorn_isolated(app, host=host, port=port)
        except BaseException as exc:  # pragma: no cover - surfaced after join
            errors.append(exc)

    thread = threading.Thread(
        target=_serve,
        name="banking-control-uvicorn",
        daemon=False,
    )
    thread.start()
    thread.join()
    if errors:
        raise errors[0]
