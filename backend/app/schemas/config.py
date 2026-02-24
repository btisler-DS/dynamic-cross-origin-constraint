"""Pydantic schemas for configuration and presets."""

from __future__ import annotations

from pydantic import BaseModel


class SimConfigSchema(BaseModel):
    seed: int = 42
    num_epochs: int = 100
    episodes_per_epoch: int = 10
    grid_size: int = 20
    num_obstacles: int = 8
    z_layers: int = 8
    max_steps: int = 100
    energy_budget: float = 100.0
    move_cost: float = 1.0
    collision_penalty: float = 5.0
    signal_dim: int = 8
    hidden_dim: int = 64
    learning_rate: float = 1e-3
    gamma: float = 0.99
    communication_tax_rate: float = 0.01
    survival_bonus: float = 0.1


class PresetResponse(BaseModel):
    name: str
    description: str
    constraints: list[str]
    config: SimConfigSchema
