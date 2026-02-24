"""Perturbation controls — the "mic drop" tests from the PDF.

- Double metabolic cost
- Flip axes
- Add noise to signals
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import torch

from ..environment import Environment
from ..comm_buffer import CommBuffer


class PerturbationType(str, Enum):
    DOUBLE_METABOLIC_COST = "double_metabolic_cost"
    FLIP_AXES = "flip_axes"
    SIGNAL_NOISE = "signal_noise"


@dataclass
class PerturbationEvent:
    epoch: int
    perturbation_type: str
    params: dict
    active: bool = True


class PerturbationManager:
    """Manages active perturbations to the simulation."""

    def __init__(self, environment: Environment, comm_buffer: CommBuffer):
        self.environment = environment
        self.comm_buffer = comm_buffer
        self.active_perturbations: list[PerturbationEvent] = []
        self._original_move_cost: float | None = None
        self._original_collision_penalty: float | None = None
        self._noise_std: float = 0.0
        self._axes_flipped: bool = False

    def apply(
        self, perturbation_type: PerturbationType, epoch: int, params: dict | None = None
    ) -> PerturbationEvent:
        """Apply a perturbation to the simulation."""
        params = params or {}

        if perturbation_type == PerturbationType.DOUBLE_METABOLIC_COST:
            self._original_move_cost = self.environment.config.move_cost
            self._original_collision_penalty = self.environment.config.collision_penalty
            self.environment.config.move_cost *= 2.0
            self.environment.config.collision_penalty *= 2.0

        elif perturbation_type == PerturbationType.FLIP_AXES:
            self._axes_flipped = True

        elif perturbation_type == PerturbationType.SIGNAL_NOISE:
            self._noise_std = params.get("noise_std", 0.5)

        event = PerturbationEvent(
            epoch=epoch,
            perturbation_type=perturbation_type.value,
            params=params,
        )
        self.active_perturbations.append(event)
        return event

    def remove(self, perturbation_type: PerturbationType, epoch: int) -> PerturbationEvent | None:
        """Remove a perturbation."""
        if perturbation_type == PerturbationType.DOUBLE_METABOLIC_COST:
            if self._original_move_cost is not None:
                self.environment.config.move_cost = self._original_move_cost
                self.environment.config.collision_penalty = self._original_collision_penalty or 5.0
                self._original_move_cost = None

        elif perturbation_type == PerturbationType.FLIP_AXES:
            self._axes_flipped = False

        elif perturbation_type == PerturbationType.SIGNAL_NOISE:
            self._noise_std = 0.0

        event = PerturbationEvent(
            epoch=epoch,
            perturbation_type=perturbation_type.value,
            params={},
            active=False,
        )
        self.active_perturbations.append(event)
        return event

    def maybe_add_noise(self, signal: torch.Tensor) -> torch.Tensor:
        """Add Gaussian noise to signals if noise perturbation is active."""
        if self._noise_std > 0:
            noise = torch.randn_like(signal) * self._noise_std
            return signal + noise
        return signal

    def maybe_flip_action(self, action: int) -> int:
        """Flip movement axes if perturbation is active (swap up/down, left/right)."""
        if self._axes_flipped:
            flip_map = {0: 1, 1: 0, 2: 3, 3: 2, 4: 4}
            return flip_map.get(action, action)
        return action

    def get_events(self) -> list[dict]:
        return [
            {
                "epoch": e.epoch,
                "type": e.perturbation_type,
                "params": e.params,
                "active": e.active,
            }
            for e in self.active_perturbations
        ]
