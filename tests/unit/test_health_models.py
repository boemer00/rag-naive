"""Unit tests for health models and services."""

import json
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.health.models import (
    Base,
    DailySummary,
    DeviceProvider,
    Insight,
    MetricType,
    NormalizedSample,
    RawSample,
)
from src.health.normalization import MetricNormalizer, SleepQualityCalculator
from src.health.repository import HealthRepository


@pytest.fixture
def db_session():
    """Create in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def repository(db_session):
    """Create repository instance."""
    return HealthRepository(db_session)


def test_raw_sample_creation():
    """Test creating a raw sample."""
    sample = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="hrv_rmssd",
        value=45.2,
        unit="ms",
        start_time=datetime.utcnow(),
        source_id="test_source"
    )

    assert sample.provider == DeviceProvider.APPLE_HEALTH
    assert sample.metric_type == "hrv_rmssd"
    assert sample.value == 45.2
    assert sample.unit == "ms"


def test_normalized_sample_creation():
    """Test creating a normalized sample."""
    sample = NormalizedSample(
        metric_type=MetricType.HRV_RMSSD,
        value=42.5,
        unit="ms",
        start_time=datetime.utcnow(),
        provenance=json.dumps({"source": "apple_health"}),
        calibration_version="v1.0"
    )

    assert sample.metric_type == MetricType.HRV_RMSSD
    assert sample.value == 42.5
    assert sample.calibration_version == "v1.0"


def test_repository_add_raw_sample(repository):
    """Test adding raw sample to repository."""
    sample = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="hrv_rmssd",
        value=50.0,
        unit="ms",
        start_time=datetime.utcnow()
    )

    saved = repository.add_raw_sample(sample)
    assert saved.id is not None
    assert saved.value == 50.0


def test_repository_get_raw_samples(repository):
    """Test retrieving raw samples with filters."""
    # Add test samples
    now = datetime.utcnow()
    samples = [
        RawSample(
            provider=DeviceProvider.APPLE_HEALTH,
            metric_type="hrv_rmssd",
            value=45.0,
            unit="ms",
            start_time=now - timedelta(days=1)
        ),
        RawSample(
            provider=DeviceProvider.APPLE_HEALTH,
            metric_type="vo2max",
            value=55.0,
            unit="mL/kg/min",
            start_time=now
        )
    ]

    repository.add_raw_samples(samples)

    # Test metric type filter
    hrv_samples = repository.get_raw_samples(metric_type="hrv_rmssd")
    assert len(hrv_samples) == 1
    assert hrv_samples[0].value == 45.0

    # Test no filter
    all_samples = repository.get_raw_samples()
    assert len(all_samples) == 2


def test_repository_daily_summary(repository):
    """Test daily summary operations."""
    summary = DailySummary(
        date="2024-01-15",
        hrv_rmssd_avg=42.5,
        vo2max_latest=55.0,
        sleep_duration=7.5,
        sleep_score=85.0
    )

    saved = repository.upsert_daily_summary(summary)
    assert saved.date == "2024-01-15"
    assert saved.hrv_rmssd_avg == 42.5

    # Test update
    updated = DailySummary(
        date="2024-01-15",
        hrv_rmssd_avg=43.0,  # Updated value
        sleep_score=90.0     # Updated value
    )

    updated_saved = repository.upsert_daily_summary(updated)
    assert updated_saved.hrv_rmssd_avg == 43.0
    assert updated_saved.sleep_score == 90.0
    assert updated_saved.vo2max_latest == 55.0  # Should preserve existing


def test_repository_insights(repository):
    """Test insight operations."""
    insight = Insight(
        kind="hrv_decline",
        message="Your HRV has declined significantly.",
        severity="warning",
        evidence=json.dumps({"change_pct": -20.0})
    )

    saved = repository.add_insight(insight)
    assert saved.id is not None
    assert saved.acknowledged is False

    # Test retrieval
    recent = repository.get_recent_insights(limit=10)
    assert len(recent) == 1
    assert recent[0].kind == "hrv_decline"

    # Test acknowledgment
    success = repository.acknowledge_insight(saved.id)
    assert success is True

    unacknowledged = repository.get_unacknowledged_insights()
    assert len(unacknowledged) == 0


def test_metric_normalizer_hrv_rmssd():
    """Test HRV RMSSD normalization."""
    normalizer = MetricNormalizer()

    raw = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="hrv_rmssd",
        value=45.0,
        unit="ms",
        start_time=datetime.utcnow()
    )

    normalized = normalizer.normalize_sample(raw)
    assert normalized is not None
    assert normalized.metric_type == MetricType.HRV_RMSSD
    assert normalized.value == 45.0
    assert normalized.unit == "ms"


def test_metric_normalizer_hrv_sdnn():
    """Test HRV SDNN to RMSSD conversion."""
    normalizer = MetricNormalizer()

    raw = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="hrv_sdnn",
        value=50.0,
        unit="ms",
        start_time=datetime.utcnow()
    )

    normalized = normalizer.normalize_sample(raw)
    assert normalized is not None
    assert normalized.metric_type == MetricType.HRV_RMSSD
    assert normalized.value == 42.5  # 50.0 * 0.85
    assert normalized.unit == "ms"

    # Check provenance
    provenance = json.loads(normalized.provenance)
    assert provenance["conversion"] == "sdnn_to_rmssd"
    assert provenance["conversion_factor"] == 0.85
    assert provenance["raw_value"] == 50.0


def test_metric_normalizer_vo2max():
    """Test VO2 max normalization."""
    normalizer = MetricNormalizer()

    raw = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="vo2max",
        value=55.0,
        unit="mL/kg/min",
        start_time=datetime.utcnow()
    )

    normalized = normalizer.normalize_sample(raw)
    assert normalized is not None
    assert normalized.metric_type == MetricType.VO2MAX_MLKGMIN
    assert normalized.value == 55.0
    assert normalized.unit == "mL/kg/min"


def test_metric_normalizer_invalid_vo2max():
    """Test VO2 max validation."""
    normalizer = MetricNormalizer()

    # Value too high
    raw = RawSample(
        provider=DeviceProvider.APPLE_HEALTH,
        metric_type="vo2max",
        value=150.0,  # Unrealistic
        unit="mL/kg/min",
        start_time=datetime.utcnow()
    )

    normalized = normalizer.normalize_sample(raw)
    assert normalized is None  # Should reject invalid values


def test_sleep_quality_calculator():
    """Test sleep quality scoring."""
    calculator = SleepQualityCalculator()

    # Good sleep
    score = calculator.calculate_sleep_score(
        duration_hours=8.0,
        efficiency_pct=90.0,
        deep_sleep_pct=20.0,
        rem_sleep_pct=22.0,
        awakenings=1,
        sleep_latency_min=10.0
    )

    assert 85 <= score <= 100  # Should be a high score

    # Poor sleep
    poor_score = calculator.calculate_sleep_score(
        duration_hours=5.0,  # Too short
        efficiency_pct=70.0,  # Low efficiency
        awakenings=8,  # Too many awakenings
        sleep_latency_min=60.0  # Long latency
    )

    assert poor_score < 60  # Should be a low score


def test_sleep_quality_duration_only():
    """Test sleep scoring with duration only."""
    calculator = SleepQualityCalculator()

    # Optimal duration
    score = calculator.calculate_sleep_score(duration_hours=8.0)
    assert score == 100.0

    # Short sleep
    short_score = calculator.calculate_sleep_score(duration_hours=5.0)
    assert short_score < 100.0

    # Long sleep
    long_score = calculator.calculate_sleep_score(duration_hours=11.0)
    assert long_score < 100.0
