"""Agent B: Conv3D spatial processor.

Perceives a 3D volumetric density map (the "Volumetric Echo").
Emits signals via Normal distribution (head defined in BaseAgent).

Bug Fix #6: Uses AdaptiveAvgPool3d(4) instead of hardcoded grid=10 Linear,
making the agent size-independent.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from .base_agent import BaseAgent


class AgentB(BaseAgent):
    """CNN agent processing 3D volumetric observations."""

    def __init__(
        self,
        signal_dim: int = 8,
        hidden_dim: int = 64,
        num_incoming: int = 2,
    ):
        super().__init__(name="B", signal_dim=signal_dim, hidden_dim=hidden_dim)
        self.hidden_dim = hidden_dim

        # 3D convolution for volumetric input
        self.conv3d = nn.Sequential(
            nn.Conv3d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv3d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            # Bug Fix #6: AdaptiveAvgPool3d for size independence
            nn.AdaptiveAvgPool3d(4),
        )

        # Flatten 32 * 4 * 4 * 4 = 2048
        self.spatial_encoder = nn.Linear(32 * 4 * 4 * 4, hidden_dim)

        # Incoming signal encoder
        self.signal_encoder = nn.Linear(signal_dim * num_incoming, hidden_dim)

        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
        )

    def encode(
        self,
        observation: torch.Tensor,
        incoming_signals: torch.Tensor,
    ) -> torch.Tensor:
        """Encode volumetric observation. Returns fused trunk."""
        # observation shape: (1, Z, H, W)
        if observation.dim() == 4:
            observation = observation.unsqueeze(0)  # add batch dim

        spatial = self.conv3d(observation)
        spatial = spatial.view(spatial.size(0), -1)
        spatial_enc = torch.relu(self.spatial_encoder(spatial)).squeeze(0)

        sig_enc = torch.relu(self.signal_encoder(incoming_signals))
        return self.fusion(torch.cat([spatial_enc, sig_enc], dim=-1))
