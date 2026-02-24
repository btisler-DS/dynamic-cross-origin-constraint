"""Tests for REINFORCE — including Bug Fix #1 (tensor loss accumulation)."""

import torch
import pytest

from simulation.agents import AgentA
from simulation.training.reinforce import compute_reinforce_loss


def test_reinforce_loss_is_tensor():
    """Bug Fix #1: loss must be a tensor, not int 0."""
    agent = AgentA(obs_dim=11, signal_dim=8)
    agent.log_probs = [torch.tensor(-0.5, requires_grad=True) for _ in range(5)]
    agent.rewards = [1.0, 0.5, 0.2, -0.1, -0.3]

    loss = compute_reinforce_loss(agent)
    assert isinstance(loss, torch.Tensor), "Loss should be a tensor, not int!"
    assert loss.requires_grad, "Loss should require grad!"


def test_reinforce_loss_empty():
    agent = AgentA(obs_dim=11, signal_dim=8)
    loss = compute_reinforce_loss(agent)
    assert isinstance(loss, torch.Tensor)


def test_reinforce_loss_backward():
    """Verify loss can be backpropagated."""
    agent = AgentA(obs_dim=11, signal_dim=8)
    agent.log_probs = [torch.tensor(-0.5, requires_grad=True)]
    agent.rewards = [1.0]

    loss = compute_reinforce_loss(agent)
    loss.backward()  # Should not raise
