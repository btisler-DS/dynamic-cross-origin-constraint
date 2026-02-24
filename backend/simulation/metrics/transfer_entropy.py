"""Transfer entropy for all 6 directed agent pairs.

Commandment #3: TE must be recorded for all directed pairs.
We expect near-zero TE at baseline. When learning activates,
asymmetry (C listening to B more than A) proves relational hierarchy.
"""

from __future__ import annotations

import numpy as np
import torch


def compute_transfer_entropy(
    source: np.ndarray,
    target: np.ndarray,
    lag: int = 1,
    num_bins: int = 10,
) -> float:
    """Compute transfer entropy from source → target.

    TE(X→Y) = H(Y_t | Y_{t-lag}) - H(Y_t | Y_{t-lag}, X_{t-lag})

    Uses binned estimation.
    """
    if len(source) < lag + 2 or len(target) < lag + 2:
        return 0.0

    n = min(len(source), len(target)) - lag

    # Discretize
    src_bins = np.digitize(source, np.linspace(source.min() - 1e-8, source.max() + 1e-8, num_bins + 1)) - 1
    tgt_bins = np.digitize(target, np.linspace(target.min() - 1e-8, target.max() + 1e-8, num_bins + 1)) - 1

    # Build joint and conditional distributions
    y_t = tgt_bins[lag:][:n]
    y_past = tgt_bins[:-lag][:n]
    x_past = src_bins[:-lag][:n]

    # P(y_t, y_past, x_past)
    joint_3d = np.zeros((num_bins, num_bins, num_bins))
    for i in range(n):
        joint_3d[y_t[i], y_past[i], x_past[i]] += 1

    total = joint_3d.sum()
    if total == 0:
        return 0.0
    joint_3d /= total

    # Marginals
    p_ypast_xpast = joint_3d.sum(axis=0)  # P(y_past, x_past)
    p_yt_ypast = joint_3d.sum(axis=2)  # P(y_t, y_past)
    p_ypast = joint_3d.sum(axis=(0, 2))  # P(y_past)

    te = 0.0
    for yt in range(num_bins):
        for yp in range(num_bins):
            for xp in range(num_bins):
                p_joint = joint_3d[yt, yp, xp]
                if p_joint > 0 and p_ypast_xpast[yp, xp] > 0 and p_ypast[yp] > 0 and p_yt_ypast[yt, yp] > 0:
                    te += p_joint * np.log2(
                        (p_joint * p_ypast[yp])
                        / (p_ypast_xpast[yp, xp] * p_yt_ypast[yt, yp])
                    )

    return float(max(te, 0.0))


def compute_all_pairs_te(
    signal_history: list[dict[str, torch.Tensor]],
    lag: int = 1,
    num_bins: int = 10,
) -> dict[str, float]:
    """Compute TE for all 6 directed pairs (A→B, A→C, B→A, B→C, C→A, C→B)."""
    # Aggregate signals per agent
    agent_signals: dict[str, list[float]] = {}

    for snapshot in signal_history:
        for name, signal in snapshot.items():
            if name not in agent_signals:
                agent_signals[name] = []
            # Use mean of signal vector as scalar summary
            agent_signals[name].append(signal.mean().item())

    agents = sorted(agent_signals.keys())
    result = {}

    for src in agents:
        for tgt in agents:
            if src != tgt:
                src_arr = np.array(agent_signals.get(src, []))
                tgt_arr = np.array(agent_signals.get(tgt, []))
                te = compute_transfer_entropy(src_arr, tgt_arr, lag, num_bins)
                result[f"{src}→{tgt}"] = te

    return result
