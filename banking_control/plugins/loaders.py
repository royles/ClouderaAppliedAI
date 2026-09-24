from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from banking_control.plugins.manager import PluginManager

logger = logging.getLogger(__name__)


def load_all_plugins(manager: PluginManager) -> None:
    """Load built-in plugins and any setuptools entry points."""
    importlib.import_module("banking_control.plugins.builtins").register(manager)
    _load_entry_points(manager)


def _load_entry_points(manager: PluginManager) -> None:
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return

    eps = entry_points()
    group = eps.select(group="banking_control.plugins") if hasattr(eps, "select") else eps.get(
        "banking_control.plugins", []
    )
    for ep in group:
        try:
            register = ep.load()
            if callable(register):
                register(manager)
            elif hasattr(register, "register"):
                manager.register_plugin(register)
            logger.info("Loaded banking_control plugin: %s", ep.name)
        except Exception:
            logger.exception("Failed to load plugin entry point: %s", ep.name)
