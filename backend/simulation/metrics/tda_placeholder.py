"""TDA placeholder — feature-flagged stub for Giotto-tda/Gudhi integration.

This module provides the interface for topological data analysis of the
emergent communication protocol. Actual TDA computation is deferred
until giotto-tda or gudhi is installed.
"""

from __future__ import annotations

import numpy as np
import torch

TDA_ENABLED = False

try:
    import gtda  # noqa: F401
    TDA_ENABLED = True
except ImportError:
    pass


def compute_persistence_diagram(
    signal_history: list[dict[str, torch.Tensor]],
) -> dict | None:
    """Compute persistence diagram of signal space topology.

    Returns None if TDA libraries are not installed.
    """
    if not TDA_ENABLED:
        return None

    # Placeholder: would use giotto-tda VietorisRipsPersistence here
    return {"status": "tda_available", "diagrams": []}


def is_tda_available() -> bool:
    return TDA_ENABLED
