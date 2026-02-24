"""Control Deck API — launch and monitor simulations from the Neural Loom UI.

Single concurrent run. State is held in memory; the frontend polls /live every
5 s to receive accumulated epoch data and run status.

Every run is also persisted to the database (same path as Dashboard runs):
  - A Run record is created at launch; its ID is stored in _state["run_id"]
  - Each epoch writes an EpochLog with full metrics + hash chain
  - On completion/stop/failure the Run status is updated

This means any run started from the Control Deck appears in Dashboard History
and is loadable in the Loom via GET /api/runs/{id}/loom.

Thread safety:
  - _lock guards all reads/writes to _state
  - DB writes happen outside the lock (using their own SessionLocal)
  - engine.stop() is safe to call from any thread
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from simulation.engine import SimulationEngine, SimulationConfig
from ..db import SessionLocal
from ..models import Run, EpochLog
from ..services.hash_chain import compute_hash, canonical_json, GENESIS_HASH

router = APIRouter(prefix="/api/control", tags=["control"])

# ── State ──────────────────────────────────────────────────────────────────────

RunStatus = Literal["idle", "running", "completed", "stopped", "failed"]

_state: dict = {
    "status":        "idle",
    "protocol":      1,
    "current_epoch": 0,
    "total_epochs":  0,
    "live_epochs":   [],
    "engine":        None,
    "error":         None,
    "run_id":        None,   # DB run ID for the active run
}
_lock = threading.Lock()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sf(v) -> float | None:
    """Safe float — handles numpy scalars gracefully."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _make_loom_epoch(m: dict, protocol: int) -> dict:
    """Extract Loom-relevant fields from a full engine epoch metrics dict.

    Used for the in-memory live_epochs list (5 s polling).
    The full dict `m` is what gets written to the DB.
    """
    inq = m.get("inquiry") or {}
    td  = inq.get("type_distribution") or {}
    return {
        "epoch":         int(m.get("epoch", 0)),
        "type_entropy":  _sf(inq.get("type_entropy"))            if protocol == 1 else None,
        "D":             _sf(td.get("DECLARE"))                  if protocol == 1 else None,
        "Q":             _sf(td.get("QUERY"))                    if protocol == 1 else None,
        "R":             _sf(td.get("RESPOND"))                  if protocol == 1 else None,
        "qrc":           _sf(inq.get("query_response_coupling")) if protocol == 1 else None,
        "inquiry_roi":   _sf(inq.get("inquiry_roi"))             if protocol == 1 else None,
        "survival_rate": _sf(m.get("survival_rate")),
        "energy_roi":    _sf(m.get("energy_roi")),
        # PCA requires a global fit across all epochs — not available during
        # live streaming. Load a saved report file to see PCA projections.
        "signal_pca": None,
    }


def _detect_crystallization(epochs: list[dict]) -> int | None:
    """First epoch in a streak of 5 consecutive epochs with type_entropy < 0.95."""
    streak_start = None
    count = 0
    for ep in epochs:
        te = ep.get("type_entropy")
        if te is not None and te < 0.95:
            if count == 0:
                streak_start = ep["epoch"]
            count += 1
            if count >= 5:
                return streak_start
        else:
            count = 0
            streak_start = None
    return None


def _db_create_run(config: "StartConfig") -> int:
    """Create a Run record in the DB and return its ID."""
    db = SessionLocal()
    try:
        run = Run(
            seed=config.seed,
            status="running",
            params_json=json.dumps({
                "seed":       config.seed,
                "num_epochs": config.epochs,
                "episodes_per_epoch": config.episodes,
                "protocol":   config.protocol,
                "source":     "control_deck",
            }),
            total_epochs=config.epochs,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id
    finally:
        db.close()


def _db_write_epoch(run_id: int, metrics: dict, seed: int, prev_hash: str) -> str:
    """Write one EpochLog row; returns the new hash for chaining."""
    current_hash = compute_hash(prev_hash, metrics, seed)
    db = SessionLocal()
    try:
        log = EpochLog(
            run_id=run_id,
            epoch=int(metrics.get("epoch", 0)),
            metrics_json=canonical_json(metrics),
            hash=current_hash,
            prev_hash=prev_hash,
        )
        db.add(log)
        run = db.query(Run).get(run_id)
        if run:
            run.current_epoch = int(metrics.get("epoch", 0)) + 1
            run.final_hash    = current_hash
        db.commit()
    finally:
        db.close()
    return current_hash


def _db_finish_run(run_id: int, status: str) -> None:
    """Mark the Run record as completed / stopped / failed."""
    db = SessionLocal()
    try:
        run = db.query(Run).get(run_id)
        if run:
            run.status       = status
            run.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# ── Request model ──────────────────────────────────────────────────────────────

class StartConfig(BaseModel):
    epochs:   int = 100
    episodes: int = 10
    seed:     int = 42
    protocol: int = 1


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/start")
def start_run(config: StartConfig):
    """Launch a new simulation in a background thread.

    Creates a DB Run record immediately; returns {ok, run_id, protocol, epochs}.
    Poll /live for progress.
    """
    with _lock:
        if _state["status"] == "running":
            return {"ok": False, "error": "A run is already in progress. Stop it first."}
        _state.update(
            status="running",
            protocol=config.protocol,
            current_epoch=0,
            total_epochs=config.epochs,
            live_epochs=[],
            engine=None,
            error=None,
            run_id=None,
        )

    # Create DB record (outside lock — no contention yet)
    run_id = _db_create_run(config)
    with _lock:
        _state["run_id"] = run_id

    def _run():
        prev_hash = GENESIS_HASH

        try:
            def _epoch_cb(m: dict) -> None:
                nonlocal prev_hash

                epoch_idx = int(m.get("epoch", 0))

                # ── In-memory live list (for polling) ──────────────────────
                with _lock:
                    _state["current_epoch"] = epoch_idx
                    _state["live_epochs"].append(
                        _make_loom_epoch(m, config.protocol)
                    )

                # ── DB persistence (outside lock) ──────────────────────────
                prev_hash = _db_write_epoch(run_id, m, config.seed, prev_hash)

            sim_config = SimulationConfig(
                seed=config.seed,
                num_epochs=config.epochs,
                episodes_per_epoch=config.episodes,
                protocol=config.protocol,
            )
            engine = SimulationEngine(config=sim_config, epoch_callback=_epoch_cb)
            with _lock:
                _state["engine"] = engine

            engine.run()  # blocks until done (or stopped)

            with _lock:
                final_status = _state["status"]
                if final_status == "running":
                    _state["status"] = "completed"
                    final_status = "completed"

            _db_finish_run(run_id, final_status)

        except Exception as exc:  # noqa: BLE001
            with _lock:
                _state["status"] = "failed"
                _state["error"]  = str(exc)
            _db_finish_run(run_id, "failed")

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "run_id": run_id, "protocol": config.protocol, "epochs": config.epochs}


@router.post("/stop")
def stop_run():
    """Signal the running simulation to stop after the current epoch."""
    with _lock:
        engine = _state.get("engine")
        if engine is not None:
            engine.stop()
        if _state["status"] == "running":
            _state["status"] = "stopped"
    return {"ok": True}


@router.get("/live")
def live_data():
    """Return current run status and all accumulated epoch data.

    Call every 5 s from the frontend Live Mode polling loop.
    Also returns the DB run_id so the frontend can link to Dashboard History.
    """
    with _lock:
        epochs = list(_state["live_epochs"])
        return {
            "status":               _state["status"],
            "protocol":             _state["protocol"],
            "current_epoch":        _state["current_epoch"],
            "total_epochs":         _state["total_epochs"],
            "epochs":               epochs,
            "crystallization_epoch": _detect_crystallization(epochs),
            "error":                _state["error"],
            "run_id":               _state["run_id"],
        }
