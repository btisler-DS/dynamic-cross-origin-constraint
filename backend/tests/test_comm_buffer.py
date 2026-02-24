"""Tests for comm buffer — including Bug Fix #2 (gradient isolation)."""

import torch
import pytest

from simulation.comm_buffer import CommBuffer, CommBufferConfig


@pytest.fixture
def buffer():
    return CommBuffer(CommBufferConfig(signal_dim=8))


def test_send_detaches_gradients(buffer):
    """Bug Fix #2: signals must be detached before storing."""
    signal = torch.randn(8, requires_grad=True)
    buffer.send("A", signal)
    stored = buffer._buffer["A"]
    assert not stored.requires_grad, "Stored signal should not require grad!"


def test_receive_excludes_self(buffer):
    buffer.send("A", torch.randn(8))
    buffer.send("B", torch.randn(8))
    received = buffer.receive("A")
    assert "A" not in received
    assert "B" in received


def test_kill_switch_zeros_signals(buffer):
    buffer.send("A", torch.ones(8))
    buffer.send("B", torch.ones(8))
    buffer.kill()
    received = buffer.receive("A")
    for sig in received.values():
        assert (sig == 0).all(), "Kill switch should zero all signals"


def test_restore_after_kill(buffer):
    buffer.send("A", torch.ones(8))
    buffer.send("B", torch.ones(8) * 5.0)
    buffer.kill()
    buffer.restore()
    received = buffer.receive("A")
    assert (received["B"] == 5.0).all()


def test_history_recording(buffer):
    buffer.send("A", torch.randn(8))
    buffer.record_history()
    assert len(buffer.history) == 1
    buffer.send("A", torch.randn(8))
    buffer.record_history()
    assert len(buffer.history) == 2
