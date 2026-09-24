from __future__ import annotations

from banking_control.plugins.manager import PluginManager
from banking_control.tools.schemas.providers import DefaultSchemaProvider, SimilarityKeySchemaProvider
from banking_control.tools.simulators.base import GenericSimulator
from banking_control.tools.simulators.specialized import SimilarityKeySimulator


def register(manager: PluginManager) -> None:
    """Register default schema providers and simulators (always loaded)."""
    manager.register_schema_provider(SimilarityKeySchemaProvider())
    manager.register_schema_provider(DefaultSchemaProvider())
    manager.register_simulator(SimilarityKeySimulator())
    manager.register_simulator(GenericSimulator())
