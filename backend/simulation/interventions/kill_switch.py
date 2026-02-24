"""Ablation kill switch — sever communication mid-run.

Proves the emergent protocol is load-bearing: if severing communication
causes performance to drop, the agents were genuinely using the protocol.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..comm_buffer import CommBuffer


@dataclass
class KillSwitchEvent:
    epoch: int
    action: str  # "kill" or "restore"
    reason: str = ""


class KillSwitch:
    """Manages communication severance for ablation testing."""

    def __init__(self, comm_buffer: CommBuffer):
        self.comm_buffer = comm_buffer
        self.events: list[KillSwitchEvent] = []

    def kill(self, epoch: int, reason: str = "manual") -> KillSwitchEvent:
        """Sever all inter-agent communication."""
        self.comm_buffer.kill()
        event = KillSwitchEvent(epoch=epoch, action="kill", reason=reason)
        self.events.append(event)
        return event

    def restore(self, epoch: int, reason: str = "manual") -> KillSwitchEvent:
        """Restore inter-agent communication."""
        self.comm_buffer.restore()
        event = KillSwitchEvent(epoch=epoch, action="restore", reason=reason)
        self.events.append(event)
        return event

    @property
    def is_killed(self) -> bool:
        return self.comm_buffer.is_killed

    def get_events(self) -> list[dict]:
        return [
            {"epoch": e.epoch, "action": e.action, "reason": e.reason}
            for e in self.events
        ]
