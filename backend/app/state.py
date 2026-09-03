"""In-memory runtime state for model/region selection (secrets stay in env)."""

from threading import Lock

from app.config import get_settings


class RuntimeState:
    """Thread-safe mutable config that clients can adjust without touching secrets."""

    def __init__(self) -> None:
        settings = get_settings()
        self._lock = Lock()
        self._model_id = settings.default_model_id
        self._region = settings.aws_region

    def get_model_id(self) -> str:
        with self._lock:
            return self._model_id

    def get_region(self) -> str:
        with self._lock:
            return self._region

    def set_model_id(self, model_id: str) -> None:
        with self._lock:
            self._model_id = model_id

    def set_region(self, region: str) -> None:
        with self._lock:
            self._region = region


runtime_state = RuntimeState()
