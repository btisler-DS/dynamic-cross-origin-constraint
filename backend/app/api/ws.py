"""WebSocket endpoint for live metrics streaming."""

from __future__ import annotations

import asyncio
import json
import logging
import queue as thread_queue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.run_manager import run_manager, _STREAM_END

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/runs/{run_id}/stream")
async def metrics_stream(websocket: WebSocket, run_id: int):
    """Stream live epoch metrics for a running simulation."""
    await websocket.accept()

    q = run_manager.get_queue(run_id)
    if q is None:
        await websocket.send_json({"error": "Run not found or not streaming"})
        await websocket.close()
        return

    try:
        while True:
            # Poll the thread-safe queue from the async context
            try:
                metrics = await asyncio.to_thread(_blocking_get, q, timeout=5.0)
            except thread_queue.Empty:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
                continue

            if metrics is _STREAM_END:
                # Simulation ended
                await websocket.send_json({"type": "complete"})
                break

            await websocket.send_json({
                "type": "epoch",
                "data": _serialize_metrics(metrics),
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for run {run_id}")
    except Exception as e:
        logger.error(f"WebSocket error for run {run_id}: {e}")


def _blocking_get(q: thread_queue.Queue, timeout: float):
    """Blocking get with timeout — runs inside asyncio.to_thread."""
    return q.get(timeout=timeout)


def _serialize_metrics(metrics: dict) -> dict:
    """Ensure all metric values are JSON serializable (recursive)."""
    return _make_serializable(metrics)


def _make_serializable(value):
    if value is None:
        return None
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, dict):
        return {k: _make_serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_make_serializable(v) for v in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value
