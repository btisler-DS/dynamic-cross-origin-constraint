"""Run SQLAlchemy model."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum
from sqlalchemy.orm import relationship

from ..db import Base


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    seed = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending, running, paused, completed, stopped, failed
    params_json = Column(Text, nullable=False)
    preset_name = Column(String(50), nullable=True)
    final_hash = Column(String(64), nullable=True)
    current_epoch = Column(Integer, default=0)
    total_epochs = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    epoch_logs = relationship("EpochLog", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

    @property
    def params(self) -> dict:
        return json.loads(self.params_json)

    @params.setter
    def params(self, value: dict) -> None:
        self.params_json = json.dumps(value)
