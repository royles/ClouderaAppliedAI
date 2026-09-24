"""FastAPI entrypoint — delegates to modular application factory."""

from banking_control.api.factory import create_app

app = create_app()
