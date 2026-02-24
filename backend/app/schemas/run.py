"""Pydantic schemas for simulation runs."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    seed: int = 42
    num_epochs: int = 100
    episodes_per_epoch: int = 10
    protocol: int = 1
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
    preset_name: str | None = None


class RunResponse(BaseModel):
    id: int
    seed: int
    status: str
    preset_name: str | None
    current_epoch: int
    total_epochs: int
    final_hash: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RunListResponse(BaseModel):
    runs: list[RunResponse]
    total: int


class RunDetail(RunResponse):
    params: dict

    model_config = {"from_attributes": True}
