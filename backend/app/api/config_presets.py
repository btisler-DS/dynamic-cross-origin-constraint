"""Preset configuration endpoints."""

from __future__ import annotations

from dataclasses import asdict
from fastapi import APIRouter

from ..schemas.config import PresetResponse, SimConfigSchema
from simulation.presets.deep_sea import DEEP_SEA_CONFIG, DEEP_SEA_META
from simulation.presets.aerial import AERIAL_CONFIG, AERIAL_META
from simulation.presets.social import SOCIAL_CONFIG, SOCIAL_META

router = APIRouter(prefix="/api/presets", tags=["presets"])

PRESETS = {
    "deep_sea": (DEEP_SEA_CONFIG, DEEP_SEA_META),
    "aerial": (AERIAL_CONFIG, AERIAL_META),
    "social": (SOCIAL_CONFIG, SOCIAL_META),
}


@router.get("", response_model=list[PresetResponse])
def list_presets():
    """List all available presets."""
    result = []
    for key, (config, meta) in PRESETS.items():
        result.append(PresetResponse(
            name=meta["name"],
            description=meta["description"],
            constraints=meta["constraints"],
            config=SimConfigSchema(**asdict(config)),
        ))
    return result
