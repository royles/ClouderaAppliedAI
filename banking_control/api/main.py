"""ASGI app for ``uvicorn banking_control.api.main:app`` (CAI subprocess launcher)."""

from banking_control.api.factory import create_app

app = create_app()
