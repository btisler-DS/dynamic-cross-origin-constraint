"""Tests for metrics — including Bug Fix #3 (entropy normalization)."""

import torch
import numpy as np
import pytest

from simulation.metrics.shannon_entropy import compute_signal_entropy
from simulation.metrics.mutual_information import compute_mutual_information
from simulation.metrics.transfer_entropy import compute_transfer_entropy
from simulation.metrics.zipf_analysis import compute_zipf_fit
from simulation.metrics.energy_roi import compute_energy_roi


def test_entropy_normalized_probabilities():
    """Bug Fix #3: entropy must work on probabilities, not raw counts."""
    # Uniform distribution should have max entropy
    signals = torch.rand(1000)
    entropy = compute_signal_entropy(signals, num_bins=10)
    assert entropy > 0, "Entropy should be positive for random signals"

    # Constant signal should have zero entropy
    constant = torch.ones(100) * 5.0
    entropy_const = compute_signal_entropy(constant, num_bins=10)
    assert entropy_const == 0.0, "Constant signal should have zero entropy"


def test_entropy_empty_signals():
    signals = torch.tensor([])
    assert compute_signal_entropy(signals) == 0.0


def test_mutual_information_positive():
    # Correlated signals should have positive MI
    x = torch.randn(500)
    y = x + torch.randn(500) * 0.1  # highly correlated
    mi = compute_mutual_information(x, y)
    assert mi > 0, "Correlated signals should have positive MI"


def test_mutual_information_independent():
    # Independent signals should have ~0 MI
    x = torch.randn(1000)
    y = torch.randn(1000)
    mi = compute_mutual_information(x, y)
    assert mi < 0.5, "Independent signals should have low MI"


def test_transfer_entropy_basic():
    source = np.random.randn(200)
    target = np.random.randn(200)
    te = compute_transfer_entropy(source, target)
    assert te >= 0, "TE should be non-negative"


def test_zipf_fit():
    # Power-law-like distribution
    signals = torch.tensor(np.random.zipf(2.0, 1000).astype(np.float32))
    result = compute_zipf_fit(signals)
    assert "alpha" in result
    assert "r_squared" in result
    assert result["alpha"] > 0


def test_energy_roi():
    assert compute_energy_roi(0.5, 100.0) == 0.005
    assert compute_energy_roi(0.0, 100.0) == 0.0
    assert compute_energy_roi(1.0, 0.0) == 0.0
