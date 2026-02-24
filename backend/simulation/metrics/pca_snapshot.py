"""PCA signal snapshot collection for post-hoc visualisation.

Samples raw 8-dim signal vectors from each epoch's communication buffer
history, then fits a global PCA across all epochs to produce 2D projections
that can be visualised in the Neural Loom UI.

The global fit ensures a consistent coordinate frame across epochs — so
cluster formation and crystallisation are visible as motion in a stable space.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import Tensor


def collect_signal_samples(
    history: list[dict[str, Tensor]],
    type_history: list[dict[str, int]],
    max_per_agent: int = 20,
) -> list[dict]:
    """Sample up to max_per_agent signals per agent from one epoch's history.

    Args:
        history:      Per-step signal dicts from CommBuffer.history.
        type_history: Per-step type dicts from CommBuffer.type_history.
        max_per_agent: Maximum samples to collect per agent name.

    Returns:
        List of {agent, vector: list[float], type_int} dicts.
    """
    if not history:
        return []

    agent_counts: dict[str, int] = {}
    samples: list[dict] = []

    for step_idx, step in enumerate(history):
        types_at_step = type_history[step_idx] if step_idx < len(type_history) else {}
        for agent_name, signal in step.items():
            count = agent_counts.get(agent_name, 0)
            if count >= max_per_agent:
                continue
            agent_counts[agent_name] = count + 1
            vec = signal.tolist() if isinstance(signal, Tensor) else list(signal)
            samples.append({
                'agent': agent_name,
                'vector': vec,
                'type_int': types_at_step.get(agent_name, 0),
            })

    return samples


def fit_pca_and_project(
    all_samples: list[list[dict]],
) -> list[list[dict]]:
    """Fit a global PCA on all epoch samples and return per-epoch 2D projections.

    Fitting globally ensures the coordinate frame is stable across epochs,
    making cluster drift visible on the scrubber.

    Args:
        all_samples: List indexed by epoch; each element is the output of
                     collect_signal_samples() for that epoch.

    Returns:
        Per-epoch list of {pc1, pc2, type_int, agent} dicts.
        Returns a list of empty lists if there are fewer than 3 total samples.
    """
    if not all_samples:
        return []

    # Flatten all vectors and track per-epoch boundaries
    all_vectors: list[list[float]] = []
    all_meta: list[dict] = []
    epoch_boundaries: list[tuple[int, int]] = []

    offset = 0
    for epoch_samples in all_samples:
        start = offset
        for s in epoch_samples:
            all_vectors.append(s['vector'])
            all_meta.append({'agent': s['agent'], 'type_int': s['type_int']})
        offset += len(epoch_samples)
        epoch_boundaries.append((start, offset))

    n_total = len(all_vectors)
    if n_total < 3:
        return [[] for _ in all_samples]

    X = np.array(all_vectors, dtype=np.float32)

    # PCA via SVD (numerically equivalent to sklearn PCA, no extra dependency)
    X_centered = X - X.mean(axis=0, keepdims=True)
    try:
        # full_matrices=False: economy SVD — Vt shape is (min(N,D), D)
        _, _, Vt = np.linalg.svd(X_centered, full_matrices=False)
        pc1_vec = Vt[0]
        pc2_vec = Vt[1] if Vt.shape[0] > 1 else np.zeros_like(Vt[0])
        pc1 = (X_centered @ pc1_vec).tolist()
        pc2 = (X_centered @ pc2_vec).tolist()
    except np.linalg.LinAlgError:
        return [[] for _ in all_samples]

    # Split back into per-epoch projections
    result: list[list[dict]] = []
    for start, end in epoch_boundaries:
        epoch_proj = [
            {
                'pc1': float(pc1[i]),
                'pc2': float(pc2[i]),
                'type_int': all_meta[i]['type_int'],
                'agent': all_meta[i]['agent'],
            }
            for i in range(start, end)
        ]
        result.append(epoch_proj)

    return result
