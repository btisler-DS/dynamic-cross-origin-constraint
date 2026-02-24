"""SHA-256 hash chain for tamper-evident epoch logging.

hash_N = SHA-256( hash_{N-1} | canonical_json(epoch_N_metrics) | run_seed )
Genesis hash uses "0" * 64 as previous.
"""

from __future__ import annotations

import hashlib
import json

GENESIS_HASH = "0" * 64


def canonical_json(data: dict) -> str:
    """Produce deterministic JSON serialization."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(prev_hash: str, metrics: dict, run_seed: int) -> str:
    """Compute SHA-256 hash for an epoch."""
    payload = f"{prev_hash}|{canonical_json(metrics)}|{run_seed}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_chain(epoch_metrics_list: list[dict], run_seed: int) -> list[dict]:
    """Build a full hash chain from epoch metrics.

    Returns list of {epoch, hash, prev_hash, metrics_json}.
    """
    chain = []
    prev_hash = GENESIS_HASH

    for metrics in epoch_metrics_list:
        current_hash = compute_hash(prev_hash, metrics, run_seed)
        chain.append({
            "epoch": metrics.get("epoch", len(chain)),
            "hash": current_hash,
            "prev_hash": prev_hash,
            "metrics_json": canonical_json(metrics),
        })
        prev_hash = current_hash

    return chain


def verify_chain(chain: list[dict], run_seed: int) -> tuple[bool, int | None]:
    """Verify integrity of a hash chain.

    Returns (is_valid, first_invalid_epoch).
    """
    prev_hash = GENESIS_HASH

    for entry in chain:
        metrics = json.loads(entry["metrics_json"])
        expected_hash = compute_hash(prev_hash, metrics, run_seed)

        if entry["hash"] != expected_hash:
            return False, entry["epoch"]
        if entry["prev_hash"] != prev_hash:
            return False, entry["epoch"]

        prev_hash = entry["hash"]

    return True, None
