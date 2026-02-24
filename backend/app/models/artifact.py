"""Artifact model — tracks generated files (reports, weights, etc.)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from ..db import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    artifact_type = Column(String(30), nullable=False)  # pdf_report, json_report, weights
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("Run", back_populates="artifacts")
