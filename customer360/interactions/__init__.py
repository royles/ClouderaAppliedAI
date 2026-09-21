"""Customer interaction events (synthetic seed + analytics)."""

from customer360.interactions.seed import build_interaction_events
from customer360.interactions.summary import load_interaction_bundle

__all__ = ["build_interaction_events", "load_interaction_bundle"]
