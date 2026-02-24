"""Energy ROI tracking — Success per Joule.

The paper's primary efficiency metric: how much task success
is achieved per unit of metabolic (energy) cost.
"""

from __future__ import annotations


def compute_energy_roi(
    target_reached_rate: float,
    avg_energy_spent: float,
) -> float:
    """Compute energy ROI: success rate per unit energy spent.

    Returns 0.0 if no energy was spent.
    """
    if avg_energy_spent <= 0:
        return 0.0
    return target_reached_rate / avg_energy_spent


def compute_cumulative_roi(
    epoch_metrics: list[dict],
) -> list[float]:
    """Compute cumulative energy ROI across epochs."""
    cumulative_success = 0.0
    cumulative_energy = 0.0
    rois = []

    for m in epoch_metrics:
        cumulative_success += m.get("target_reached_rate", 0.0)
        cumulative_energy += m.get("avg_energy_spent", 0.0)
        if cumulative_energy > 0:
            rois.append(cumulative_success / cumulative_energy)
        else:
            rois.append(0.0)

    return rois
