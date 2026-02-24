"""Agent C: Cross-modal attention (GNN-inspired) agent.

Perceives pairwise relational features between all entities.
Uses attention over incoming signals — the "translator" agent.
Emits signals and actions from heads defined in BaseAgent.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .base_agent import BaseAgent


class AgentC(BaseAgent):
    """Cross-modal attention agent processing relational features."""

    def __init__(
        self,
        obs_dim: int,
        signal_dim: int = 8,
        hidden_dim: int = 64,
        num_incoming: int = 2,
    ):
        super().__init__(name="C", signal_dim=signal_dim, hidden_dim=hidden_dim)
        self.hidden_dim = hidden_dim
        self.num_incoming = num_incoming

        # Relational feature encoder
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Per-signal attention mechanism
        self.signal_key = nn.Linear(signal_dim, hidden_dim)
        self.signal_value = nn.Linear(signal_dim, hidden_dim)
        self.obs_query = nn.Linear(hidden_dim, hidden_dim)

        # Fusion after attention
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
        )

    def encode(
        self,
        observation: torch.Tensor,
        incoming_signals: torch.Tensor,
    ) -> torch.Tensor:
        """Encode relational observation with cross-modal attention. Returns fused trunk.

        Agent C's type choice is informed by attention-weighted context from
        both other agents' signals before choosing to query or respond.
        """
        obs_enc = self.obs_encoder(observation)

        # Split incoming signals into per-agent signals
        signals = incoming_signals.view(self.num_incoming, self.signal_dim)

        # Cross-modal attention: observation queries, signals are keys/values
        query = self.obs_query(obs_enc).unsqueeze(0)  # (1, hidden)
        keys = self.signal_key(signals)               # (num_incoming, hidden)
        values = self.signal_value(signals)           # (num_incoming, hidden)

        # Scaled dot-product attention
        scale = self.hidden_dim ** 0.5
        attn_weights = torch.softmax(
            (query @ keys.T) / scale, dim=-1
        )  # (1, num_incoming)
        attended = (attn_weights @ values).squeeze(0)  # (hidden,)

        return self.fusion(torch.cat([obs_enc, attended], dim=-1))
