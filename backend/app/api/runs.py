"""CRUD endpoints for simulation runs."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Run, EpochLog
from ..schemas.run import RunCreate, RunResponse, RunListResponse, RunDetail
from ..schemas.metrics import EpochMetrics, HashChainEntry, HashChainVerifyResponse
from ..services.run_manager import run_manager
from ..services.hash_chain import verify_chain
from simulation.engine import SimulationConfig

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=RunResponse)
async def create_run(body: RunCreate, db: Session = Depends(get_db)):
    """Create and start a new simulation run."""
    config = SimulationConfig(
        seed=body.seed,
        num_epochs=body.num_epochs,
        episodes_per_epoch=body.episodes_per_epoch,
        grid_size=body.grid_size,
        num_obstacles=body.num_obstacles,
        z_layers=body.z_layers,
        max_steps=body.max_steps,
        energy_budget=body.energy_budget,
        move_cost=body.move_cost,
        collision_penalty=body.collision_penalty,
        signal_dim=body.signal_dim,
        hidden_dim=body.hidden_dim,
        learning_rate=body.learning_rate,
        gamma=body.gamma,
        communication_tax_rate=body.communication_tax_rate,
        survival_bonus=body.survival_bonus,
    )

    run = Run(
        seed=body.seed,
        status="pending",
        params_json=json.dumps(body.model_dump()),
        preset_name=body.preset_name,
        total_epochs=body.num_epochs,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Start simulation
    await run_manager.start_run(run.id, config)

    return run


@router.get("", response_model=RunListResponse)
def list_runs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all runs with pagination."""
    total = db.query(Run).count()
    runs = db.query(Run).order_by(Run.created_at.desc()).offset(skip).limit(limit).all()
    return RunListResponse(runs=runs, total=total)


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Get run details."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunDetail(
        id=run.id,
        seed=run.seed,
        status=run.status,
        preset_name=run.preset_name,
        current_epoch=run.current_epoch,
        total_epochs=run.total_epochs,
        final_hash=run.final_hash,
        created_at=run.created_at,
        updated_at=run.updated_at,
        completed_at=run.completed_at,
        params=run.params,
    )


@router.delete("/{run_id}")
def delete_run(run_id: int, db: Session = Depends(get_db)):
    """Delete a run and its artifacts."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Stop if running
    run_manager.stop_run(run_id)

    db.delete(run)
    db.commit()
    return {"detail": "Run deleted"}


@router.post("/{run_id}/stop")
def stop_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run_manager.stop_run(run_id)
    run.status = "stopped"
    db.commit()
    return {"detail": "Run stopped"}


@router.post("/{run_id}/pause")
def pause_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run_manager.pause_run(run_id)
    run.status = "paused"
    db.commit()
    return {"detail": "Run paused"}


@router.post("/{run_id}/resume")
def resume_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run_manager.resume_run(run_id)
    run.status = "running"
    db.commit()
    return {"detail": "Run resumed"}


@router.get("/{run_id}/epochs")
def get_epochs(run_id: int, db: Session = Depends(get_db)):
    """Get all epoch metrics for a run."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = (
        db.query(EpochLog)
        .filter(EpochLog.run_id == run_id)
        .order_by(EpochLog.epoch)
        .all()
    )
    return [
        {
            "epoch": log.epoch,
            "metrics": log.metrics,
            "hash": log.hash,
        }
        for log in logs
    ]


@router.get("/{run_id}/hash-chain")
def get_hash_chain(run_id: int, db: Session = Depends(get_db)):
    """Get the full hash chain for a run."""
    logs = (
        db.query(EpochLog)
        .filter(EpochLog.run_id == run_id)
        .order_by(EpochLog.epoch)
        .all()
    )
    return [
        {
            "epoch": log.epoch,
            "hash": log.hash,
            "prev_hash": log.prev_hash,
            "metrics_json": log.metrics_json,
        }
        for log in logs
    ]


@router.post("/{run_id}/hash-chain/verify", response_model=HashChainVerifyResponse)
def verify_hash_chain(run_id: int, db: Session = Depends(get_db)):
    """Verify integrity of a run's hash chain."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = (
        db.query(EpochLog)
        .filter(EpochLog.run_id == run_id)
        .order_by(EpochLog.epoch)
        .all()
    )

    chain = [
        {
            "epoch": log.epoch,
            "hash": log.hash,
            "prev_hash": log.prev_hash,
            "metrics_json": log.metrics_json,
        }
        for log in logs
    ]

    is_valid, first_invalid = verify_chain(chain, run.seed)

    return HashChainVerifyResponse(
        valid=is_valid,
        total_epochs=len(chain),
        first_invalid_epoch=first_invalid,
        message="Chain is valid" if is_valid else f"Chain broken at epoch {first_invalid}",
    )
