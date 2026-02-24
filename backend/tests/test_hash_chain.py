"""Tests for SHA-256 hash chain integrity."""

import json
import pytest

from app.services.hash_chain import (
    compute_hash,
    build_chain,
    verify_chain,
    GENESIS_HASH,
    canonical_json,
)


def test_genesis_hash():
    assert len(GENESIS_HASH) == 64
    assert GENESIS_HASH == "0" * 64


def test_hash_deterministic():
    metrics = {"epoch": 0, "value": 1.23}
    h1 = compute_hash(GENESIS_HASH, metrics, 42)
    h2 = compute_hash(GENESIS_HASH, metrics, 42)
    assert h1 == h2


def test_hash_changes_with_seed():
    metrics = {"epoch": 0, "value": 1.23}
    h1 = compute_hash(GENESIS_HASH, metrics, 42)
    h2 = compute_hash(GENESIS_HASH, metrics, 99)
    assert h1 != h2


def test_build_and_verify_chain():
    metrics_list = [
        {"epoch": i, "value": i * 1.5}
        for i in range(10)
    ]
    chain = build_chain(metrics_list, run_seed=42)
    assert len(chain) == 10
    assert chain[0]["prev_hash"] == GENESIS_HASH

    is_valid, first_invalid = verify_chain(chain, run_seed=42)
    assert is_valid
    assert first_invalid is None


def test_tamper_detection():
    metrics_list = [
        {"epoch": i, "value": i * 1.5}
        for i in range(10)
    ]
    chain = build_chain(metrics_list, run_seed=42)

    # Tamper with epoch 5's metrics
    tampered = json.loads(chain[5]["metrics_json"])
    tampered["value"] = 999.0
    chain[5]["metrics_json"] = canonical_json(tampered)

    is_valid, first_invalid = verify_chain(chain, run_seed=42)
    assert not is_valid
    assert first_invalid == 5


def test_canonical_json_deterministic():
    d1 = {"b": 2, "a": 1}
    d2 = {"a": 1, "b": 2}
    assert canonical_json(d1) == canonical_json(d2)
