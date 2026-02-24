"""Report download endpoints — PDF and JSON."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Run, EpochLog, Artifact
from ..config import settings
from ..services.report_generator import generate_pdf_report, generate_json_report, generate_markdown_report
from ..services.weight_exporter import export_weights
from ..services.run_manager import run_manager

router = APIRouter(prefix="/api/runs/{run_id}", tags=["reports"])


@router.get("/report/json")
def download_json_report(run_id: int, db: Session = Depends(get_db)):
    """Generate and download JSON report."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = db.query(EpochLog).filter(EpochLog.run_id == run_id).order_by(EpochLog.epoch).all()
    epoch_metrics = [log.metrics for log in logs]

    run_data = {
        "id": run.id,
        "seed": run.seed,
        "status": run.status,
        "final_hash": run.final_hash,
        "created_at": str(run.created_at),
        "params": run.params,
    }

    report_json = generate_json_report(run_data, epoch_metrics)
    return JSONResponse(content=json.loads(report_json))


@router.get("/report/pdf")
def download_pdf_report(run_id: int, db: Session = Depends(get_db)):
    """Generate and download PDF report."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = db.query(EpochLog).filter(EpochLog.run_id == run_id).order_by(EpochLog.epoch).all()
    epoch_metrics = [log.metrics for log in logs]

    run_data = {
        "id": run.id,
        "seed": run.seed,
        "status": run.status,
        "final_hash": run.final_hash,
        "created_at": str(run.created_at),
        "params": run.params,
    }

    output_path = str(Path(settings.data_dir) / f"reports/run_{run_id}.pdf")
    generate_pdf_report(run_data, epoch_metrics, output_path)

    # Track artifact
    artifact = Artifact(run_id=run_id, artifact_type="pdf_report", file_path=output_path)
    db.add(artifact)
    db.commit()

    return FileResponse(output_path, filename=f"run_{run_id}_report.pdf", media_type="application/pdf")


@router.get("/report/md")
def download_markdown_report(run_id: int, db: Session = Depends(get_db)):
    """Generate and download Markdown report."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = db.query(EpochLog).filter(EpochLog.run_id == run_id).order_by(EpochLog.epoch).all()
    epoch_metrics = [log.metrics for log in logs]

    run_data = {
        "id": run.id,
        "seed": run.seed,
        "status": run.status,
        "final_hash": run.final_hash,
        "created_at": str(run.created_at),
        "params": run.params,
    }

    md_content = generate_markdown_report(run_data, epoch_metrics)
    output_path = str(Path(settings.data_dir) / f"reports/run_{run_id}_report.md")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(md_content, encoding="utf-8")

    return FileResponse(output_path, filename=f"run_{run_id}_report.md", media_type="text/markdown")


@router.get("/weights")
def download_weights(run_id: int, db: Session = Depends(get_db)):
    """Download model weights."""
    run = db.query(Run).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    engine = run_manager.get_engine(run_id)
    if not engine:
        raise HTTPException(status_code=400, detail="No active engine — run may have been garbage collected")

    output_path = str(Path(settings.data_dir) / f"weights/run_{run_id}.pt")
    weights = engine.get_agent_weights()
    export_weights(weights, output_path, metadata={"run_id": run_id, "seed": run.seed})

    artifact = Artifact(run_id=run_id, artifact_type="weights", file_path=output_path)
    db.add(artifact)
    db.commit()

    return FileResponse(output_path, filename=f"run_{run_id}_weights.pt")
