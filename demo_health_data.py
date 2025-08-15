#!/usr/bin/env python3
"""Generate demo health data to show the platform functionality."""

import json
from datetime import datetime, timedelta

from src.health.database import get_db_session
from src.health.models import DeviceProvider, MetricType, NormalizedSample, RawSample
from src.health.repository import HealthRepository
from src.health.service import HealthService


def create_demo_data():
    """Create realistic demo health data."""
    with next(get_db_session()) as session:
        repo = HealthRepository(session)

        # Generate 30 days of sample data
        base_date = datetime.utcnow() - timedelta(days=30)

        print("Creating demo health data...")
        # Generate HRV data (realistic RMSSD values)
        hrv_base = 45.0  # Base HRV in ms
        for i in range(30):
            date = base_date + timedelta(days=i)
            # Simulate natural variation with slight trend
            variation = (i * 0.1) + (i % 7) * 2  # Weekly pattern + slight improvement
            noise = (hash(str(date.date())) % 20 - 10) * 0.5  # Random daily variation
            hrv_value = max(25, hrv_base + variation + noise)

            raw_sample = RawSample(
                provider=DeviceProvider.APPLE_HEALTH,
                metric_type="hrv_rmssd",
                value=hrv_value,
                unit="ms",
                start_time=date,
                source_id=f"demo_hrv_{i}"
            )
            repo.add_raw_sample(raw_sample)

            # Add normalized version
            normalized = NormalizedSample(
                metric_type=MetricType.HRV_RMSSD,
                value=hrv_value,
                unit="ms",
                start_time=date,
                provenance=json.dumps({"source": "apple_health", "demo": True}),
                calibration_version="v1.0"
            )
            repo.add_normalized_sample(normalized)

        # Generate VO2 max data (realistic values)
        vo2_base = 52.0  # Base VO2 max
        for i in range(0, 30, 7):  # Weekly measurements
            date = base_date + timedelta(days=i)
            # Simulate slight improvement over time
            trend = i * 0.05
            noise = (hash(str(date.date())) % 10 - 5) * 0.2
            vo2_value = max(35, min(65, vo2_base + trend + noise))

            raw_sample = RawSample(
                provider=DeviceProvider.APPLE_HEALTH,
                metric_type="vo2max",
                value=vo2_value,
                unit="mL/kg/min",
                start_time=date,
                source_id=f"demo_vo2_{i}"
            )
            repo.add_raw_sample(raw_sample)

            normalized = NormalizedSample(
                metric_type=MetricType.VO2MAX_MLKGMIN,
                value=vo2_value,
                unit="mL/kg/min",
                start_time=date,
                provenance=json.dumps({"source": "apple_health", "demo": True}),
                calibration_version="v1.0"
            )
            repo.add_normalized_sample(normalized)

        # Generate sleep data
        sleep_base = 7.5  # Base sleep duration in hours
        for i in range(30):
            date = base_date + timedelta(days=i)
            # Simulate weekend vs weekday patterns
            is_weekend = date.weekday() >= 5
            weekend_bonus = 0.5 if is_weekend else 0
            noise = (hash(str(date.date())) % 20 - 10) * 0.05
            sleep_value = max(5, min(10, sleep_base + weekend_bonus + noise))

            raw_sample = RawSample(
                provider=DeviceProvider.APPLE_HEALTH,
                metric_type="sleep_stage",
                value=sleep_value,
                unit="hours",
                start_time=date,
                source_id=f"demo_sleep_{i}"
            )
            repo.add_raw_sample(raw_sample)

            normalized = NormalizedSample(
                metric_type=MetricType.SLEEP_DURATION,
                value=sleep_value,
                unit="hours",
                start_time=date,
                provenance=json.dumps({"source": "apple_health", "demo": True}),
                calibration_version="v1.0"
            )
            repo.add_normalized_sample(normalized)

        print("✅ Demo data created successfully!")
        print(f"📊 Generated data for {30} days")
        print(f"💓 HRV samples: {30}")
        print(f"🫁 VO₂ max samples: {5}")
        print(f"😴 Sleep samples: {30}")

def generate_summaries_and_insights():
    """Generate daily summaries and insights from the demo data."""
    with next(get_db_session()) as session:
        service = HealthService(session)
        print("\n🔄 Generating daily summaries and insights...")

        # Update daily summaries
        summaries = service._update_daily_summaries(days_back=35)
        print(f"📈 Created {len(summaries)} daily summaries")

        # Generate insights
        insights = service._generate_insights()
        print(f"💡 Generated {len(insights)} insights")
        # Print insights
        if insights:
            print("\n🔍 Generated Insights:")
            for insight in insights:
                emoji = "⚠️" if insight.severity == "warning" else "ℹ️"
                print(f"{emoji} {insight.kind}: {insight.message}")

if __name__ == "__main__":
    create_demo_data()
    generate_summaries_and_insights()
    print("\n🌐 Server running at: http://localhost:8000")
    print("📊 Dashboard: open web/frontend/index.html in your browser")
