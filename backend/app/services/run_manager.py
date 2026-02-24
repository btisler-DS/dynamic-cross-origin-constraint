"""Simulation lifecycle manager with thread-safe queue for real-time streaming."""

from __future__ import annotations

import asyncio
import json
import logging
import queue as thread_queue
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import Run, EpochLog
from ..db import SessionLocal
from .hash_chain import compute_hash, GENESIS_HASH, canonical_json
from simulation.engine import SimulationEngine, SimulationConfig
from simulation.metrics.transfer_entropy import compute_all_pairs_te
from simulation.metrics.zipf_analysis import compute_zipf_per_agent
from simulation.metrics.energy_roi import compute_energy_roi

logger = logging.getLogger(__name__)

# Sentinel to signal end of stream
_STREAM_END = object()


class RunManager:
    """Manages simulation runs in background threads."""

    def __init__(self):
        self._engines: dict[int, SimulationEngine] = {}
        self._queues: dict[int, thread_queue.Queue] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    async def start_run(self, run_id: int, config: SimulationConfig) -> thread_queue.Queue:
        """Start a simulation run in a background thread."""
        q: thread_queue.Queue = thread_queue.Queue(maxsize=200)
        self._queues[run_id] = q

        engine = SimulationEngine(config=config)
        self._engines[run_id] = engine

        task = asyncio.create_task(self._run_in_thread(run_id, engine, q))
        self._tasks[run_id] = task

        return q

    async def _run_in_thread(
        self, run_id: int, engine: SimulationEngine, q: thread_queue.Queue
    ) -> None:
        """Run simulation in a thread, pushing metrics to queue."""
        db = SessionLocal()
        prev_hash = GENESIS_HASH

        try:
            # Update run status
            run = db.query(Run).get(run_id)
            if run:
                run.status = "running"
                db.commit()

            def epoch_callback(metrics: dict) -> None:
                nonlocal prev_hash

                # Compute extended metrics from comm buffer history
                # NOTE: engine._run_epoch computes entropy/MI then resets buffer,
                # but the callback fires AFTER reset. TE/Zipf/ROI use the
                # already-computed metrics or operate on the epoch-level data.
                roi = compute_energy_roi(
                    metrics.get("target_reached_rate", 0.0),
                    metrics.get("avg_energy_spent", 0.0),
                )
                metrics["energy_roi"] = roi

                # TE and Zipf need signal history; supply empty defaults
                # if not already present (will be populated once engine
                # is updated to pass them through)
                metrics.setdefault("transfer_entropy", {})
                metrics.setdefault("zipf", {})

                # Compute hash
                current_hash = compute_hash(prev_hash, metrics, engine.config.seed)

                # Save to DB
                epoch_log = EpochLog(
                    run_id=run_id,
                    epoch=metrics["epoch"],
                    metrics_json=canonical_json(metrics),
                    hash=current_hash,
                    prev_hash=prev_hash,
                )
                db.add(epoch_log)

                # Update run
                run_record = db.query(Run).get(run_id)
                if run_record:
                    run_record.current_epoch = metrics["epoch"] + 1  # 1-based count of completed epochs
                    run_record.final_hash = current_hash
                db.commit()

                prev_hash = current_hash

                # Thread-safe push to queue
                try:
                    q.put_nowait(metrics)
                except thread_queue.Full:
                    # Drop oldest to make room
                    try:
                        q.get_nowait()
                    except thread_queue.Empty:
                        pass
                    q.put_nowait(metrics)

            engine.epoch_callback = epoch_callback

            # Run simulation in thread
            await asyncio.to_thread(engine.run)

            # Mark complete
            run = db.query(Run).get(run_id)
            if run:
                run.status = "completed"
                run.completed_at = datetime.utcnow()
                db.commit()

        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}", exc_info=True)
            run = db.query(Run).get(run_id)
            if run:
                run.status = "failed"
                db.commit()
        finally:
            db.close()
            # Signal end of stream (thread-safe)
            q.put(_STREAM_END)

    def stop_run(self, run_id: int) -> bool:
        engine = self._engines.get(run_id)
        if engine:
            engine.stop()
            return True
        return False

    def pause_run(self, run_id: int) -> bool:
        engine = self._engines.get(run_id)
        if engine:
            engine.pause()
            return True
        return False

    def resume_run(self, run_id: int) -> bool:
        engine = self._engines.get(run_id)
        if engine:
            engine.resume()
            return True
        return False

    def kill_communication(self, run_id: int) -> bool:
        engine = self._engines.get(run_id)
        if engine:
            engine.kill_communication()
            return True
        return False

    def restore_communication(self, run_id: int) -> bool:
        engine = self._engines.get(run_id)
        if engine:
            engine.restore_communication()
            return True
        return False

    def get_engine(self, run_id: int) -> SimulationEngine | None:
        return self._engines.get(run_id)

    def get_queue(self, run_id: int) -> thread_queue.Queue | None:
        return self._queues.get(run_id)


# Singleton
run_manager = RunManager()
