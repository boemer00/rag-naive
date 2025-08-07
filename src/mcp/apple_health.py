"""Apple Health XML parser for extracting key biomarkers."""

import xml.etree.ElementTree as ET
from datetime import datetime

from .health_schema import HealthMetrics


def parse_apple_health(xml_path: str) -> list[HealthMetrics]:
    """Parse Apple Health export XML and extract core biomarkers."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Group metrics by date
    daily_metrics = {}

    for record in root.findall('Record'):
        record_type = record.get('type', '')
        value = record.get('value', '')
        start_date = record.get('startDate', '')

        if not value or not start_date:
            continue

        # Extract date (YYYY-MM-DD)
        date = start_date.split(' ')[0]

        if date not in daily_metrics:
            daily_metrics[date] = HealthMetrics(date=date)

        # Map Apple Health types to our schema
        if record_type == 'HKQuantityTypeIdentifierRestingHeartRate':
            daily_metrics[date].heart_rate_resting = float(value)
        elif record_type == 'HKQuantityTypeIdentifierVO2Max':
            daily_metrics[date].vo2_max = float(value)
        elif record_type == 'HKCategoryTypeIdentifierSleepAnalysis':
            # Sleep analysis - calculate duration from startDate and endDate
            end_date = record.get('endDate', '')
            if start_date and end_date:
                start_dt = datetime.fromisoformat(start_date.replace(' +0000', ''))
                end_dt = datetime.fromisoformat(end_date.replace(' +0000', ''))
                duration_hours = (end_dt - start_dt).total_seconds() / 3600

                # Add to existing sleep duration for the date
                if daily_metrics[date].sleep_duration is None:
                    daily_metrics[date].sleep_duration = 0
                daily_metrics[date].sleep_duration += duration_hours
        elif record_type == 'HKQuantityTypeIdentifierBloodPressureSystolic':
            daily_metrics[date].blood_pressure_systolic = int(float(value))
        elif record_type == 'HKQuantityTypeIdentifierBloodPressureDiastolic':
            daily_metrics[date].blood_pressure_diastolic = int(float(value))

    return list(daily_metrics.values())


def get_latest_metrics(xml_path: str, days: int = 30) -> dict:
    """Get latest health metrics for biomarker analysis."""
    metrics = parse_apple_health(xml_path)

    # Sort by date and get recent metrics
    sorted_metrics = sorted(metrics, key=lambda x: x.date, reverse=True)
    recent = sorted_metrics[:days]

    # Calculate averages
    heart_rates = [m.heart_rate_resting for m in recent if m.heart_rate_resting]
    vo2_maxes = [m.vo2_max for m in recent if m.vo2_max]
    sleep_durations = [m.sleep_duration for m in recent if m.sleep_duration]

    return {
        "avg_resting_hr": sum(heart_rates) / len(heart_rates) if heart_rates else None,
        "latest_vo2_max": vo2_maxes[0] if vo2_maxes else None,
        "avg_sleep_duration": sum(sleep_durations) / len(sleep_durations) if sleep_durations else None,
        "days_analyzed": len(recent),
        "date_range": f"{recent[-1].date} to {recent[0].date}" if recent else None
    }
