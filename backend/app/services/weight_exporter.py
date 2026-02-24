"""Model weight export — .pt serialization for protocol inspection."""

from __future__ import annotations

from pathlib import Path

import torch


def export_weights(
    agent_weights: dict[str, dict],
    output_path: str,
    metadata: dict | None = None,
) -> str:
    """Export agent weights to a .pt file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "agent_weights": agent_weights,
        "metadata": metadata or {},
    }
    torch.save(payload, output_path)
    return output_path


def load_weights(path: str) -> dict:
    """Load agent weights from a .pt file."""
    return torch.load(path, map_location="cpu", weights_only=False)
