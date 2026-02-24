"""Protocol registry for the MARL simulation.

Protocols define the reward structure, signal type semantics, and metrics
computed per epoch. Switching protocols does NOT change the agent architecture —
only the learning dynamics and reward signals.

Protocol 0: Baseline — flat Landauer tax, no type head gradient.
Protocol 1: Interrogative Emergence — Gumbel-Softmax type head, differential costs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import torch
from torch import Tensor

from .training.reward import compute_reward
from .training.temperature import get_tau, sample_signal_type
from .metrics.inquiry_metrics import compute_inquiry_metrics


class ProtocolBase(ABC):
    """Abstract protocol interface."""

    protocol_id: int

    @abstractmethod
    def get_tau(self, epoch: int) -> float:
        """Return current Gumbel-Softmax temperature."""

    @abstractmethod
    def resolve_signal_type(
        self,
        type_logits: Tensor,
        tau: float,
        training: bool = True,
    ) -> tuple[Tensor | None, int]:
        """Determine signal type from logits.

        Returns:
            (soft_type | None, hard_type_int)
            soft_type is None for Protocol 0 (no gradient through type head).
        """

    @abstractmethod
    def compute_reward(
        self,
        *,
        agent_name: str,
        env_reward: float,
        signal_sent: Tensor,
        energy_remaining: float,
        energy_budget: float,
        communication_tax_rate: float,
        reached_target: bool,
        survival_bonus: float,
        signal_type: int,
    ) -> float:
        """Compute the reward for a single agent step."""

    @abstractmethod
    def compute_epoch_extras(
        self,
        *,
        type_history: list,
        signal_history: list,
        target_rate: float,
        tax_rate: float,
    ) -> dict:
        """Compute protocol-specific metrics for the epoch."""

    def should_train_type_head(self) -> bool:
        """Whether the type head should receive REINFORCE gradients."""
        return True


class Protocol0(ProtocolBase):
    """Baseline protocol — flat Landauer tax, no type head gradient.

    Reproduces exact Run 10 behaviour: signal_type is always 0 (DECLARE),
    the type head is frozen, and no inquiry metrics are logged.
    """

    protocol_id = 0

    def get_tau(self, epoch: int) -> float:
        return 1.0  # unused — type head frozen

    def resolve_signal_type(
        self, type_logits: Tensor, tau: float, training: bool = True
    ) -> tuple[None, int]:
        return None, 0  # Always DECLARE, no gradient

    def compute_reward(
        self,
        *,
        agent_name: str,
        env_reward: float,
        signal_sent: Tensor,
        energy_remaining: float,
        energy_budget: float,
        communication_tax_rate: float,
        reached_target: bool,
        survival_bonus: float,
        signal_type: int,
    ) -> float:
        # Flat tax — no type multiplier, identical to Run 10
        signal_cost = communication_tax_rate * signal_sent.abs().sum().item()
        energy_fraction = max(energy_remaining / energy_budget, 0.0)
        return env_reward - signal_cost + survival_bonus * energy_fraction

    def compute_epoch_extras(self, **_) -> dict:
        return {}  # No inquiry metrics for Protocol 0

    def should_train_type_head(self) -> bool:
        return False


class Protocol1(ProtocolBase):
    """Interrogative Emergence — Gumbel-Softmax, differential costs, inquiry metrics.

    Agents learn to distinguish DECLARATIVE / INTERROGATIVE / RESPONSE signals
    via a 3-way type head trained jointly with REINFORCE.

    Cost multipliers are configurable to support the five preregistered conditions:
        Baseline:      declare=1.0, query=1.5, respond=0.8
        Low Pressure:  declare=1.0, query=1.2, respond=0.9
        High Pressure: declare=1.0, query=3.0, respond=0.5
        Extreme:       declare=1.0, query=5.0, respond=0.3
    """

    protocol_id = 1

    def __init__(
        self,
        declare_cost: float = 1.0,
        query_cost: float = 1.5,
        respond_cost: float = 0.8,
    ) -> None:
        self.declare_cost = declare_cost
        self.query_cost = query_cost
        self.respond_cost = respond_cost

    def get_tau(self, epoch: int) -> float:
        return get_tau(epoch)

    def resolve_signal_type(
        self, type_logits: Tensor, tau: float, training: bool = True
    ) -> tuple[Tensor, int]:
        return sample_signal_type(type_logits, tau, training)

    def compute_reward(
        self,
        *,
        agent_name: str,
        env_reward: float,
        signal_sent: Tensor,
        energy_remaining: float,
        energy_budget: float,
        communication_tax_rate: float,
        reached_target: bool,
        survival_bonus: float,
        signal_type: int,
    ) -> float:
        return compute_reward(
            agent_name=agent_name,
            env_reward=env_reward,
            signal_sent=signal_sent,
            energy_remaining=energy_remaining,
            energy_budget=energy_budget,
            communication_tax_rate=communication_tax_rate,
            reached_target=reached_target,
            survival_bonus=survival_bonus,
            signal_type=signal_type,
            declare_cost=self.declare_cost,
            query_cost=self.query_cost,
            respond_cost=self.respond_cost,
        )

    def compute_epoch_extras(
        self,
        *,
        type_history: list,
        signal_history: list,
        target_rate: float,
        tax_rate: float,
    ) -> dict:
        return {
            'inquiry': compute_inquiry_metrics(
                type_history=type_history,
                signal_history=signal_history,
                target_reached_rate=target_rate,
                communication_tax_rate=tax_rate,
            )
        }


PROTOCOL_REGISTRY: dict[int, type[ProtocolBase]] = {
    0: Protocol0,
    1: Protocol1,
}


def create_protocol(
    protocol_id: int,
    declare_cost: float = 1.0,
    query_cost: float = 1.5,
    respond_cost: float = 0.8,
) -> ProtocolBase:
    """Instantiate a protocol by ID.

    Args:
        protocol_id:  0=Baseline, 1=Interrogative Emergence.
        declare_cost: DECLARE signal cost multiplier (Protocol 1 only).
        query_cost:   QUERY signal cost multiplier (Protocol 1 only).
        respond_cost: RESPOND signal cost multiplier (Protocol 1 only).

    Raises:
        ValueError: If protocol_id is not in PROTOCOL_REGISTRY.
    """
    if protocol_id not in PROTOCOL_REGISTRY:
        raise ValueError(
            f"Unknown protocol: {protocol_id}. "
            f"Valid IDs: {sorted(PROTOCOL_REGISTRY)}"
        )
    if protocol_id == 1:
        return Protocol1(
            declare_cost=declare_cost,
            query_cost=query_cost,
            respond_cost=respond_cost,
        )
    return PROTOCOL_REGISTRY[protocol_id]()
