"""Tests for environment — including Bug Fix #4 (density clamping)."""

import numpy as np
import torch
import pytest

from simulation.environment import Environment, EnvironmentConfig


@pytest.fixture
def env():
    config = EnvironmentConfig(grid_size=10, num_obstacles=3)
    return Environment(config)


def test_reset_returns_observations(env):
    obs = env.reset(seed=42)
    assert "A" in obs
    assert "B" in obs
    assert "C" in obs
    assert "grid" in obs


def test_agents_placed_correctly(env):
    env.reset(seed=42)
    assert len(env.agents_pos) == 3
    for name, pos in env.agents_pos.items():
        assert 0 <= pos[0] < env.grid_size
        assert 0 <= pos[1] < env.grid_size


def test_step_returns_correct_structure(env):
    env.reset(seed=42)
    actions = {"A": 0, "B": 1, "C": 4}
    obs, rewards, done, info = env.step(actions)
    assert isinstance(rewards, dict)
    assert isinstance(done, bool)
    assert "energy" in info


def test_3d_density_non_negative(env):
    """Bug Fix #4: density values must never be negative."""
    env.reset(seed=42)
    density = env.get_3d_density_map("B")
    assert (density >= 0).all(), "Density map contains negative values!"


def test_3d_density_has_gradient(env):
    """Hardware Friction Mandate: target should have z-layer gradient."""
    env.reset(seed=42)
    density = env.get_3d_density_map("B")
    tx, ty = env.target_pos
    target_values = density[0, :, tx, ty]
    # Values should decrease across z-layers (linear decay)
    if target_values[0] > 0:
        assert target_values[0] >= target_values[-1], "No gradient decay across z-layers"


def test_obstacles_are_walls(env):
    """Obstacles should be 1.0 across ALL z-layers."""
    env.reset(seed=42)
    density = env.get_3d_density_map("B")
    for obs in env.obstacles:
        values = density[0, :, obs[0], obs[1]]
        assert (values == 1.0).all(), "Obstacle not fully blocking across z-layers"


def test_energy_depletes(env):
    env.reset(seed=42)
    initial_energy = dict(env.energy)
    env.step({"A": 0, "B": 0, "C": 0})  # all move up
    for name in ["A", "B", "C"]:
        assert env.energy[name] <= initial_energy[name]
