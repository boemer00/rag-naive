"""ETL pipeline for processing health data from various sources."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from sqlalchemy.orm import Session

from .models import DeviceProvider, RawSample
from .repository import HealthRepository


class AppleHealthETL:
    """ETL pipeline for Apple Health XML exports."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = HealthRepository(session)

    def extract_from_xml(self, xml_path: str) -> list[RawSample]:
        """Extract raw samples from Apple Health XML."""
        tree = ET.parse(xml_path)
        root = tree.getroot()

        samples = []

        for record in root.findall('Record'):
            sample = self._parse_record(record)
            if sample:
                samples.append(sample)

        return samples

    def _parse_record(self, record: ET.Element) -> RawSample | None:
        """Parse a single XML record into a RawSample."""
        record_type = record.get('type', '')
        value_str = record.get('value', '')
        start_date_str = record.get('startDate', '')
        end_date_str = record.get('endDate')
        source_name = record.get('sourceName', '')

        if not value_str or not start_date_str or not record_type:
            return None

        # Map Apple Health types to our metric types
        metric_type = self._map_apple_health_type(record_type)
        if not metric_type:
            return None  # Skip unmapped types

        try:
            # Parse dates
            start_time = self._parse_apple_date(start_date_str)
            end_time = self._parse_apple_date(end_date_str) if end_date_str else None

            # Parse value based on metric type
            value, unit = self._parse_value(value_str, metric_type, record_type)

            return RawSample(
                provider=DeviceProvider.APPLE_HEALTH,
                metric_type=metric_type,
                value=value,
                unit=unit,
                start_time=start_time,
                end_time=end_time,
                source_id=source_name,
                ingested_at=datetime.utcnow()
            )

        except (ValueError, TypeError):
            return None  # Skip invalid records

    def _map_apple_health_type(self, apple_type: str) -> str | None:
        """Map Apple Health type to our metric type."""
        mapping = {
            'HKQuantityTypeIdentifierRestingHeartRate': 'hr_resting',
            'HKQuantityTypeIdentifierVO2Max': 'vo2max',
            'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'hrv_sdnn',
            'HKCategoryTypeIdentifierSleepAnalysis': 'sleep_stage',
            'HKQuantityTypeIdentifierBloodPressureSystolic': 'bp_systolic',
            'HKQuantityTypeIdentifierBloodPressureDiastolic': 'bp_diastolic',
        }
        return mapping.get(apple_type)

    def _parse_apple_date(self, date_str: str) -> datetime:
        """Parse Apple Health date format."""
        # Apple format: "2024-01-15 08:30:45 +0000"
        # Remove timezone for simplicity (assume UTC)
        clean_date = date_str.replace(' +0000', '').replace(' -0000', '')
        return datetime.fromisoformat(clean_date)

    def _parse_value(self, value_str: str, metric_type: str, apple_type: str) -> tuple[float, str]:
        """Parse value and determine unit."""
        value = float(value_str)

        # Determine unit based on metric type
        unit_mapping = {
            'hr_resting': ('bpm', value),
            'vo2max': ('mL/kg/min', value),
            'hrv_sdnn': ('ms', value),
            'bp_systolic': ('mmHg', value),
            'bp_diastolic': ('mmHg', value),
            'sleep_stage': ('category', value)  # Apple uses 0=awake, 1=core, 2=deep, 3=REM
        }

        unit, final_value = unit_mapping.get(metric_type, ('unknown', value))
        return final_value, unit

    def load_to_database(self, samples: list[RawSample]) -> int:
        """Load raw samples into database."""
        if not samples:
            return 0

        self.repo.add_raw_samples(samples)
        return len(samples)

    def process_file(self, xml_path: str) -> dict:
        """Process entire Apple Health XML file."""
        # Extract
        samples = self.extract_from_xml(xml_path)

        # Load
        loaded_count = self.load_to_database(samples)

        # Summary statistics
        metric_counts = {}
        for sample in samples:
            metric_counts[sample.metric_type] = metric_counts.get(sample.metric_type, 0) + 1

        return {
            "total_samples": len(samples),
            "loaded_samples": loaded_count,
            "metric_breakdown": metric_counts,
            "date_range": {
                "start": min(s.start_time for s in samples) if samples else None,
                "end": max(s.start_time for s in samples) if samples else None
            }
        }


def process_apple_health_export(xml_path: str) -> dict:
    """Process Apple Health export (convenience function)."""
    from .service import process_health_export
    return process_health_export(xml_path)
