"""Pydantic schemas for metrics and hash chain."""

from __future__ import annotations

from pydantic import BaseModel


class EpochMetrics(BaseModel):
    epoch: int
    avg_reward: dict[str, float]
    survival_rate: float
    target_reached_rate: float
    avg_steps: float
    avg_energy_spent: float
    losses: dict[str, float]
    entropy: dict[str, float]
    mutual_information: dict[str, float]
    transfer_entropy: dict[str, float] | None = None
    zipf: dict[str, dict[str, float]] | None = None
    energy_roi: float | None = None
    comm_killed: bool = False
    interventions: list[dict] | None = None


class HashChainEntry(BaseModel):
    epoch: int
    hash: str
    prev_hash: str
    metrics_json: str


class HashChainVerifyResponse(BaseModel):
    valid: bool
    total_epochs: int
    first_invalid_epoch: int | None = None
    message: str
