"""Metric normalization and standardization for cross-device compatibility."""

from __future__ import annotations

import json

from .models import MetricType, NormalizedSample, RawSample


class MetricNormalizer:
    """Normalizes raw metrics to canonical standards."""

    def __init__(self, calibration_version: str = "v1.0") -> None:
        self.calibration_version = calibration_version

    def normalize_samples(self, raw_samples: list[RawSample]) -> list[NormalizedSample]:
        """Normalize a list of raw samples."""
        normalized = []

        for raw in raw_samples:
            normalized_sample = self.normalize_sample(raw)
            if normalized_sample:
                normalized.append(normalized_sample)

        return normalized

    def normalize_sample(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize a single raw sample."""
        normalizer_map = {
            'hrv_rmssd': self._normalize_hrv_rmssd,
            'hrv_sdnn': self._normalize_hrv_sdnn,
            'vo2max': self._normalize_vo2max,
            'hr_resting': self._normalize_hr_resting,
            'sleep_stage': self._normalize_sleep_stage,
            'bp_systolic': self._normalize_blood_pressure,
            'bp_diastolic': self._normalize_blood_pressure,
        }

        normalizer = normalizer_map.get(raw.metric_type)
        if not normalizer:
            return None

        return normalizer(raw)

    def _normalize_hrv_rmssd(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize HRV RMSSD (already canonical)."""
        if raw.unit not in ['ms', 'milliseconds']:
            return None

        return NormalizedSample(
            metric_type=MetricType.HRV_RMSSD,
            value=raw.value,
            unit='ms',
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )

    def _normalize_hrv_sdnn(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize HRV SDNN to RMSSD equivalent."""
        if raw.unit not in ['ms', 'milliseconds']:
            return None

        # Convert SDNN to RMSSD using population averages
        # Research shows RMSSD ≈ 0.85 * SDNN for most populations
        # This is a rough conversion; per-user calibration would be better
        rmssd_equivalent = raw.value * 0.85

        return NormalizedSample(
            metric_type=MetricType.HRV_RMSSD,
            value=rmssd_equivalent,
            unit='ms',
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "conversion": "sdnn_to_rmssd",
                "conversion_factor": 0.85,
                "raw_value": raw.value,
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )

    def _normalize_vo2max(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize VO2 max to mL/kg/min."""
        if raw.unit == 'mL/kg/min':
            # Already canonical
            normalized_value = raw.value
        elif raw.unit in ['ml/kg/min', 'mlO2/kg/min']:
            # Common variations
            normalized_value = raw.value
        else:
            # Unknown unit, skip
            return None

        # Validate reasonable range (10-90 ml/kg/min for humans)
        if not (10 <= normalized_value <= 90):
            return None

        return NormalizedSample(
            metric_type=MetricType.VO2MAX_MLKGMIN,
            value=normalized_value,
            unit='mL/kg/min',
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "raw_unit": raw.unit,
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )

    def _normalize_hr_resting(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize resting heart rate."""
        if raw.unit not in ['bpm', 'beats/min']:
            return None

        # Validate reasonable range (30-120 bpm)
        if not (30 <= raw.value <= 120):
            return None

        return NormalizedSample(
            metric_type=MetricType.HR_RESTING,
            value=raw.value,
            unit='bpm',
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )

    def _normalize_sleep_stage(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize sleep stages (preserve raw for now)."""
        # TODO: Implement unified sleep stage mapping
        # For now, just pass through
        return NormalizedSample(
            metric_type=MetricType.SLEEP_DURATION,  # Temporary
            value=raw.value,
            unit=raw.unit,
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "note": "sleep_stage_normalization_pending",
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )

    def _normalize_blood_pressure(self, raw: RawSample) -> NormalizedSample | None:
        """Normalize blood pressure."""
        if raw.unit not in ['mmHg']:
            return None

        # Determine if systolic or diastolic
        if raw.metric_type == 'bp_systolic':
            metric_type = MetricType.BP_SYSTOLIC
            # Validate range (70-250 mmHg for systolic)
            if not (70 <= raw.value <= 250):
                return None
        elif raw.metric_type == 'bp_diastolic':
            metric_type = MetricType.BP_DIASTOLIC
            # Validate range (40-150 mmHg for diastolic)
            if not (40 <= raw.value <= 150):
                return None
        else:
            return None

        return NormalizedSample(
            metric_type=metric_type,
            value=raw.value,
            unit='mmHg',
            start_time=raw.start_time,
            end_time=raw.end_time,
            provenance=json.dumps({
                "source": raw.provider.value,
                "raw_metric": raw.metric_type,
                "raw_id": raw.id if hasattr(raw, 'id') else None
            }),
            calibration_version=self.calibration_version
        )


class SleepQualityCalculator:
    """Calculates unified sleep quality score (0-100)."""

    def calculate_sleep_score(
        self,
        duration_hours: float,
        efficiency_pct: float | None = None,
        deep_sleep_pct: float | None = None,
        rem_sleep_pct: float | None = None,
        awakenings: int | None = None,
        sleep_latency_min: float | None = None,
        age: int | None = None,
        gender: str | None = None
    ) -> float:
        """Calculate unified sleep score with age/gender adjustments."""

        score = 0.0
        max_score = 100.0

        # Duration score (35% weight)
        duration_score = self._score_duration(duration_hours, age)
        score += duration_score * 0.35

        # Efficiency score (25% weight)
        if efficiency_pct is not None:
            efficiency_score = self._score_efficiency(efficiency_pct)
            score += efficiency_score * 0.25
        else:
            # Reduce total possible score if missing efficiency
            max_score -= 25

        # Sleep architecture score (25% weight)
        if deep_sleep_pct is not None and rem_sleep_pct is not None:
            architecture_score = self._score_architecture(deep_sleep_pct, rem_sleep_pct, age)
            score += architecture_score * 0.25
        else:
            max_score -= 25

        # Sleep continuity score (15% weight)
        if awakenings is not None and sleep_latency_min is not None:
            continuity_score = self._score_continuity(awakenings, sleep_latency_min)
            score += continuity_score * 0.15
        else:
            max_score -= 15

        # Normalize to 0-100 based on available metrics
        if max_score < 100:
            score = (score / max_score) * 100

        return max(0.0, min(100.0, score))

    def _score_duration(self, duration_hours: float, age: int | None = None) -> float:
        """Score sleep duration (0-100)."""
        # Age-adjusted optimal ranges
        if age is None:
            optimal_range = (7.0, 9.0)  # General adult
        elif age < 18:
            optimal_range = (8.0, 10.0)  # Teens
        elif age < 65:
            optimal_range = (7.0, 9.0)  # Adults
        else:
            optimal_range = (7.0, 8.5)  # Seniors

        optimal_min, optimal_max = optimal_range

        if optimal_min <= duration_hours <= optimal_max:
            return 100.0
        elif duration_hours < optimal_min:
            # Penalty for short sleep
            shortage = optimal_min - duration_hours
            return max(0.0, 100 - (shortage * 20))  # -20 points per hour short
        else:
            # Penalty for long sleep (less severe)
            excess = duration_hours - optimal_max
            return max(0.0, 100 - (excess * 10))  # -10 points per hour excess

    def _score_efficiency(self, efficiency_pct: float) -> float:
        """Score sleep efficiency (0-100)."""
        if efficiency_pct >= 85:
            return 100.0
        elif efficiency_pct >= 80:
            return 80 + ((efficiency_pct - 80) * 4)  # Linear 80-100
        elif efficiency_pct >= 70:
            return 60 + ((efficiency_pct - 70) * 2)  # Linear 60-80
        else:
            return max(0.0, efficiency_pct * 0.857)  # Linear 0-60

    def _score_architecture(
        self,
        deep_sleep_pct: float,
        rem_sleep_pct: float,
        age: int | None = None
    ) -> float:
        """Score sleep architecture (0-100)."""
        score = 0.0

        # Deep sleep scoring (60% of architecture score)
        optimal_deep = 20.0 if age is None or age < 60 else 15.0
        deep_score = max(0.0, 100 - abs(deep_sleep_pct - optimal_deep) * 3)
        score += deep_score * 0.6

        # REM sleep scoring (40% of architecture score)
        optimal_rem = 22.0
        rem_score = max(0.0, 100 - abs(rem_sleep_pct - optimal_rem) * 2.5)
        score += rem_score * 0.4

        return score

    def _score_continuity(self, awakenings: int, sleep_latency_min: float) -> float:
        """Score sleep continuity (0-100)."""
        score = 0.0

        # Awakenings scoring (60% of continuity)
        if awakenings <= 1:
            awakening_score = 100.0
        elif awakenings <= 3:
            awakening_score = 80.0
        elif awakenings <= 5:
            awakening_score = 60.0
        else:
            awakening_score = max(0.0, 60 - (awakenings - 5) * 10)

        score += awakening_score * 0.6

        # Sleep latency scoring (40% of continuity)
        if sleep_latency_min <= 15:
            latency_score = 100.0
        elif sleep_latency_min <= 30:
            latency_score = 80.0
        elif sleep_latency_min <= 45:
            latency_score = 60.0
        else:
            latency_score = max(0.0, 60 - (sleep_latency_min - 45) * 2)

        score += latency_score * 0.4

        return score
