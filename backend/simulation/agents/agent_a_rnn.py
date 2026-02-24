"""Agent A: RNN-based sequential processor.

Perceives a 1D sequence (distances to entities).
Emits signals via Normal distribution (head defined in BaseAgent).
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .base_agent import BaseAgent


class AgentA(BaseAgent):
    """RNN agent processing 1D sequential observations."""

    def __init__(
        self,
        obs_dim: int,
        signal_dim: int = 8,
        hidden_dim: int = 64,
        num_incoming: int = 2,
    ):
        super().__init__(name="A", signal_dim=signal_dim, hidden_dim=hidden_dim)
        self.hidden_dim = hidden_dim

        # Observation encoder
        self.obs_encoder = nn.Linear(obs_dim, hidden_dim)

        # Incoming signal encoder
        self.signal_encoder = nn.Linear(signal_dim * num_incoming, hidden_dim)

        # RNN for sequential processing
        self.rnn = nn.GRUCell(hidden_dim * 2, hidden_dim)

        # Hidden state
        self.hidden = None

    def reset_hidden(self) -> None:
        self.hidden = None

    def encode(
        self,
        observation: torch.Tensor,
        incoming_signals: torch.Tensor,
    ) -> torch.Tensor:
        """Encode observation through GRU. Returns hidden state as trunk."""
        obs_enc = torch.relu(self.obs_encoder(observation))
        sig_enc = torch.relu(self.signal_encoder(incoming_signals))
        combined = torch.cat([obs_enc, sig_enc], dim=-1)

        if self.hidden is None:
            self.hidden = torch.zeros(self.hidden_dim)

        self.hidden = self.rnn(combined.unsqueeze(0), self.hidden.unsqueeze(0)).squeeze(0)
        return self.hidden

    def clear_episode(self) -> None:
        super().clear_episode()
        self.hidden = None
