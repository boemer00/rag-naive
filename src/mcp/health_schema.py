"""Simple health data schema for biomarker tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class HealthMetrics:
    """Core biomarkers from wearable devices."""
    date: str
    heart_rate_resting: Optional[float] = None
    vo2_max: Optional[float] = None
    sleep_duration: Optional[float] = None  # hours
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    source: str = "apple_health"

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "heart_rate_resting": self.heart_rate_resting,
            "vo2_max": self.vo2_max,
            "sleep_duration": self.sleep_duration,
            "blood_pressure_systolic": self.blood_pressure_systolic,
            "blood_pressure_diastolic": self.blood_pressure_diastolic,
            "source": self.source
        }