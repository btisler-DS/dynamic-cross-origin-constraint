"""Pydantic schemas for interventions."""

from __future__ import annotations

from pydantic import BaseModel


class InterventionRequest(BaseModel):
    intervention_type: str  # kill_switch, restore_comm, double_cost, flip_axes, signal_noise
    params: dict = {}


class InterventionResponse(BaseModel):
    success: bool
    intervention_type: str
    message: str
    epoch: int | None = None
