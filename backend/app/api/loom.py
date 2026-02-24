"""Loom data endpoint — serves epoch metrics filtered for Neural Loom visualisation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Run, EpochLog

router = APIRouter(prefix="/api/runs", tags=["loom"])


def _find_crystallization_epoch(epochs: list[dict]) -> int | None:
    """First epoch in a streak of 5 consecutive epochs with type_entropy < 0.95."""
    streak_start = None
    streak_count = 0
    for ep in epochs:
        te = ep.get('type_entropy')
        if te is not None and te < 0.95:
            if streak_count == 0:
                streak_start = ep['epoch']
            streak_count += 1
            if streak_count >= 5:
                return streak_start
        else:
            streak_count = 0
            streak_start = None
    return None


@router.get("/{run_id}/loom")
def get_loom_data(run_id: int, db: Session = Depends(get_db)):
    """Return epoch metrics filtered for the Neural Loom scrubber.

    Response shape:
        {
          "epochs": [{
            "epoch": int,
            "type_entropy": float | null,
            "D": float | null, "Q": float | null, "R": float | null,
            "qrc": float | null,
            "inquiry_roi": float | null,
            "survival_rate": float | null,
            "signal_pca": [{pc1, pc2, type_int, agent}] | null
          }],
          "crystallization_epoch": int | null,
          "protocol": int
        }
    """
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = (
        db.query(EpochLog)
        .filter(EpochLog.run_id == run_id)
        .order_by(EpochLog.epoch)
        .all()
    )

    epochs = []
    for log in logs:
        m = log.metrics
        inq = m.get('inquiry') or {}
        td = inq.get('type_distribution') or {}

        epochs.append({
            'epoch': log.epoch,
            'type_entropy': inq.get('type_entropy'),
            'D': td.get('DECLARE'),
            'Q': td.get('QUERY'),
            'R': td.get('RESPOND'),
            'qrc': inq.get('query_response_coupling'),
            'inquiry_roi': inq.get('inquiry_roi'),
            'survival_rate': m.get('survival_rate'),
            'energy_roi': m.get('energy_roi'),
            'signal_pca': m.get('signal_pca'),
        })

    protocol = run.params.get('protocol', 1)

    return {
        'epochs': epochs,
        'crystallization_epoch': _find_crystallization_epoch(epochs),
        'protocol': protocol,
    }
