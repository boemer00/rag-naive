"""SQLAlchemy models for health metrics storage."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class MetricType(str, Enum):
    """Canonical metric types for normalization."""
    HRV_RMSSD = "hrv_rmssd"
    HRV_SDNN = "hrv_sdnn"
    VO2MAX_MLKGMIN = "vo2max_mlkgmin"
    SLEEP_DURATION = "sleep_duration"
    SLEEP_EFFICIENCY = "sleep_efficiency"
    SLEEP_SCORE = "sleep_score_0_100"
    HR_RESTING = "hr_resting"
    BP_SYSTOLIC = "bp_systolic"
    BP_DIASTOLIC = "bp_diastolic"


class DeviceProvider(str, Enum):
    """Supported device providers."""
    APPLE_HEALTH = "apple_health"
    GARMIN = "garmin"
    OURA = "oura"
    WHOOP = "whoop"


class RawSample(Base):
    """Raw biometric samples from devices."""
    __tablename__ = "raw_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[DeviceProvider] = mapped_column(String(50), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Original record ID


class NormalizedSample(Base):
    """Normalized metrics using canonical standards."""
    __tablename__ = "normalized_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_type: Mapped[MetricType] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    provenance: Mapped[str] = mapped_column(Text, nullable=False)  # JSON: which raw samples contributed
    calibration_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DailySummary(Base):
    """Daily aggregated health metrics."""
    __tablename__ = "daily_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # YYYY-MM-DD

    # HRV metrics
    hrv_rmssd_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_rmssd_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_rmssd_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # VO2 max
    vo2max_latest: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Sleep metrics
    sleep_duration: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    sleep_efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)  # percentage
    sleep_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100

    # Heart rate
    hr_resting: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Rolling averages (7, 30 days)
    hrv_7day_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    hrv_30day_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    vo2max_30day_trend: Mapped[float | None] = mapped_column(Float, nullable=True)  # change rate

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Insight(Base):
    """Generated insights from health metrics."""
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # "hrv_drop", "vo2_improvement", etc.
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # "info", "warning", "alert"
    evidence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON with supporting data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged: Mapped[bool] = mapped_column(nullable=False, default=False)
