"""Tests for agents — including Bug Fix #6 (adaptive pooling)."""

import torch
import pytest

from simulation.agents import AgentA, AgentB, AgentC


def test_agent_a_forward():
    agent = AgentA(obs_dim=11, signal_dim=8)
    obs = torch.randn(11)
    incoming = torch.randn(16)  # 8 * 2 incoming signals
    signal, action_logits, type_logits = agent(obs, incoming)
    assert signal.shape == (8,)
    assert action_logits.shape == (5,)
    assert type_logits.shape == (3,)


def test_agent_b_forward():
    """Bug Fix #6: AgentB should work with any grid size, not just 10."""
    agent = AgentB(signal_dim=8)
    incoming = torch.randn(16)

    # Test with grid_size=10
    obs_10 = torch.randn(1, 8, 10, 10)
    signal, action_logits, type_logits = agent(obs_10, incoming)
    assert signal.shape == (8,)
    assert action_logits.shape == (5,)
    assert type_logits.shape == (3,)

    # Test with grid_size=20 (Bug Fix #6: should NOT crash)
    obs_20 = torch.randn(1, 8, 20, 20)
    signal, action_logits, type_logits = agent(obs_20, incoming)
    assert signal.shape == (8,)
    assert action_logits.shape == (5,)

    # Test with grid_size=30
    obs_30 = torch.randn(1, 8, 30, 30)
    signal, action_logits, type_logits = agent(obs_30, incoming)
    assert signal.shape == (8,)


def test_agent_c_forward():
    agent = AgentC(obs_dim=45, signal_dim=8)
    obs = torch.randn(45)
    incoming = torch.randn(16)
    signal, action_logits, type_logits = agent(obs, incoming)
    assert signal.shape == (8,)
    assert action_logits.shape == (5,)
    assert type_logits.shape == (3,)


def test_freeze_type_head():
    """Protocol 0: freeze_type_head() should disable type_head gradients."""
    agent = AgentA(obs_dim=11, signal_dim=8)
    agent.freeze_type_head()
    for p in agent.type_head.parameters():
        assert not p.requires_grad


def test_no_hardcoded_signal_action_mappings():
    """Integrity test: ensure no constant signal-to-action mappings exist."""
    import inspect
    from simulation.agents import agent_a_rnn, agent_b_cnn, agent_c_gnn

    for module in [agent_a_rnn, agent_b_cnn, agent_c_gnn]:
        source = inspect.getsource(module)
        # Should not contain patterns like "if signal == X" or signal-to-action dicts
        assert "if signal ==" not in source
        assert "signal_to_action" not in source.lower()
        assert "action_map" not in source.lower()
