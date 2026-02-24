"""Zipf's Law analysis for emergent signal distributions.

Tests whether the signal frequency distribution follows a power law,
which would indicate the emergence of a structured communication protocol.
"""

from __future__ import annotations

import numpy as np
import torch
from scipy import stats


def compute_zipf_fit(
    signals: torch.Tensor,
    num_bins: int = 50,
) -> dict[str, float]:
    """Fit Zipf's law to signal frequency distribution.

    Returns:
        alpha: Power-law exponent (Zipf exponent)
        ks_statistic: KS test statistic (lower = better fit)
        ks_pvalue: KS test p-value
        r_squared: R² of log-log linear fit
    """
    values = signals.detach().cpu().numpy().flatten()
    if len(values) < 10:
        return {"alpha": 0.0, "ks_statistic": 1.0, "ks_pvalue": 0.0, "r_squared": 0.0}

    # Bin the signals
    counts, _ = np.histogram(values, bins=num_bins)
    counts = counts[counts > 0]  # remove zero bins

    if len(counts) < 3:
        return {"alpha": 0.0, "ks_statistic": 1.0, "ks_pvalue": 0.0, "r_squared": 0.0}

    # Sort in descending order (Zipf ranking)
    sorted_counts = np.sort(counts)[::-1]
    ranks = np.arange(1, len(sorted_counts) + 1)

    # Log-log linear fit
    log_ranks = np.log(ranks)
    log_counts = np.log(sorted_counts)

    slope, intercept, r_value, p_value, std_err = stats.linregress(log_ranks, log_counts)

    # KS test: compare empirical CDF to fitted power law
    # Normalize to CDF
    empirical_cdf = np.cumsum(sorted_counts) / sorted_counts.sum()
    fitted_values = np.exp(intercept) * ranks ** slope
    fitted_cdf = np.cumsum(fitted_values) / fitted_values.sum()
    ks_stat = np.max(np.abs(empirical_cdf - fitted_cdf))

    return {
        "alpha": float(-slope),  # Zipf exponent (positive)
        "ks_statistic": float(ks_stat),
        "ks_pvalue": float(p_value),
        "r_squared": float(r_value ** 2),
    }


def compute_zipf_per_agent(
    signal_history: list[dict[str, torch.Tensor]],
    num_bins: int = 50,
) -> dict[str, dict[str, float]]:
    """Compute Zipf analysis for each agent's signals."""
    agent_signals: dict[str, list[torch.Tensor]] = {}

    for snapshot in signal_history:
        for name, signal in snapshot.items():
            if name not in agent_signals:
                agent_signals[name] = []
            agent_signals[name].append(signal)

    result = {}
    for name, sigs in agent_signals.items():
        if sigs:
            all_signals = torch.cat(sigs)
            result[name] = compute_zipf_fit(all_signals, num_bins)
        else:
            result[name] = {"alpha": 0.0, "ks_statistic": 1.0, "ks_pvalue": 0.0, "r_squared": 0.0}

    return result
