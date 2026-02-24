"""Intervention endpoints — kill switch + perturbation controls."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Run
from ..schemas.intervention import InterventionRequest, InterventionResponse
from ..services.run_manager import run_manager

router = APIRouter(prefix="/api/runs/{run_id}/interventions", tags=["interventions"])


@router.post("", response_model=InterventionResponse)
def trigger_intervention(
    run_id: int,
    body: InterventionRequest,
    db: Session = Depends(get_db),
):
    """Trigger an intervention on a running simulation."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "running":
        raise HTTPException(status_code=400, detail="Run is not currently running")

    engine = run_manager.get_engine(run_id)
    if not engine:
        raise HTTPException(status_code=400, detail="No active engine for this run")

    intervention_type = body.intervention_type

    if intervention_type == "kill_switch":
        engine.kill_communication()
        msg = "Communication severed"
    elif intervention_type == "restore_comm":
        engine.restore_communication()
        msg = "Communication restored"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown intervention: {intervention_type}")

    return InterventionResponse(
        success=True,
        intervention_type=intervention_type,
        message=msg,
        epoch=run.current_epoch,
    )
