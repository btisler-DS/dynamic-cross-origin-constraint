"""EpochLog SQLAlchemy model — stores per-epoch metrics and hash chain."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from ..db import Base


class EpochLog(Base):
    __tablename__ = "epoch_logs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    epoch = Column(Integer, nullable=False)
    metrics_json = Column(Text, nullable=False)
    hash = Column(String(64), nullable=False)
    prev_hash = Column(String(64), nullable=False)
    interventions_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="epoch_logs")

    @property
    def metrics(self) -> dict:
        return json.loads(self.metrics_json)

    @metrics.setter
    def metrics(self, value: dict) -> None:
        self.metrics_json = json.dumps(value)

    @property
    def interventions(self) -> list[dict] | None:
        if self.interventions_json:
            return json.loads(self.interventions_json)
        return None
