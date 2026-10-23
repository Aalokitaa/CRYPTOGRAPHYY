"""
CryptoScope SQLAlchemy Database Models
"""

import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from backend.app.core.database import Base

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, index=True)
    job_type = Column(String(32), nullable=False) # analysis, training, dataset_build
    status = Column(String(32), default="pending", nullable=False) # pending, running, completed, failed
    progress = Column(Integer, default=0) # 0 to 100
    step = Column(String(128), default="Queued")
    message = Column(Text, default="")
    logs_json = Column(Text, default="[]")
    result_id = Column(String(64), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), 
                        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    format = Column(String(32), nullable=False)
    isa = Column(String(32), nullable=False)
    endianness = Column(String(16), default="little")
    bits = Column(Integer, default=64)
    entrypoint = Column(String(32), default="0x0")
    confidence = Column(Float, default=1.0)
    summary_json = Column(Text, nullable=False)
    full_data_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class RunModel(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True, index=True)
    model_type = Column(String(32), nullable=False)
    dataset_version = Column(String(32), nullable=False)
    overall_f1 = Column(Float, default=0.0)
    metrics_json = Column(Text, nullable=False)
    config_json = Column(Text, nullable=False)
    model_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
