"""Binned mutual information estimator for inter-agent signal analysis."""

from __future__ import annotations

import numpy as np
import torch


def compute_mutual_information(
    signals_x: torch.Tensor,
    signals_y: torch.Tensor,
    num_bins: int = 20,
) -> float:
    """Estimate mutual information between two signal streams using binning.

    MI(X;Y) = H(X) + H(Y) - H(X,Y)
    """
    x = signals_x.detach().cpu().numpy().flatten()
    y = signals_y.detach().cpu().numpy().flatten()

    min_len = min(len(x), len(y))
    if min_len == 0:
        return 0.0
    x, y = x[:min_len], y[:min_len]

    # Joint histogram
    joint_hist, _, _ = np.histogram2d(x, y, bins=num_bins)
    joint_total = joint_hist.sum()
    if joint_total == 0:
        return 0.0

    joint_prob = joint_hist / joint_total

    # Marginals
    px = joint_prob.sum(axis=1)
    py = joint_prob.sum(axis=0)

    # MI calculation
    mi = 0.0
    for i in range(num_bins):
        for j in range(num_bins):
            if joint_prob[i, j] > 0 and px[i] > 0 and py[j] > 0:
                mi += joint_prob[i, j] * np.log2(
                    joint_prob[i, j] / (px[i] * py[j])
                )
    return float(max(mi, 0.0))


def compute_pairwise_mi(
    signal_history: list[dict[str, torch.Tensor]],
    num_bins: int = 20,
) -> dict[str, float]:
    """Compute MI for all agent pairs."""
    agent_signals: dict[str, list[torch.Tensor]] = {}

    for snapshot in signal_history:
        for name, signal in snapshot.items():
            if name not in agent_signals:
                agent_signals[name] = []
            agent_signals[name].append(signal)

    agents = sorted(agent_signals.keys())
    result = {}

    for i, a1 in enumerate(agents):
        for a2 in agents[i + 1:]:
            if agent_signals[a1] and agent_signals[a2]:
                x = torch.cat(agent_signals[a1])
                y = torch.cat(agent_signals[a2])
                mi = compute_mutual_information(x, y, num_bins)
                result[f"{a1}-{a2}"] = mi
            else:
                result[f"{a1}-{a2}"] = 0.0

    return result
