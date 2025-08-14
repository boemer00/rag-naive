"""Health service layer for coordinating data processing and insights."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from .database import get_db_session
from .etl import AppleHealthETL
from .models import DailySummary, Insight, MetricType
from .normalization import MetricNormalizer, SleepQualityCalculator
from .repository import HealthRepository


class HealthService:
    """Service for managing health data processing and analysis."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = HealthRepository(session)
        self.normalizer = MetricNormalizer()
        self.sleep_calculator = SleepQualityCalculator()

    def process_apple_health_export(self, xml_path: str) -> dict[str, Any]:
        """Process Apple Health export with normalization and summarization."""
        # Extract raw data
        etl = AppleHealthETL(self.session)
        extraction_result = etl.process_file(xml_path)

        if extraction_result["loaded_samples"] == 0:
            return extraction_result

        # Normalize recent samples
        raw_samples = self.repo.get_raw_samples(limit=10000)  # Get recent samples
        normalized_samples = self.normalizer.normalize_samples(raw_samples)

        if normalized_samples:
            self.repo.add_normalized_samples(normalized_samples)

        # Generate daily summaries
        self._update_daily_summaries()

        # Generate insights
        insights = self._generate_insights()

        return {
            **extraction_result,
            "normalized_samples": len(normalized_samples),
            "new_insights": len(insights),
            "processing_complete": True
        }

    def _update_daily_summaries(self, days_back: int = 90) -> list[DailySummary]:
        """Update daily summaries for recent dates."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        summaries = []

        # Process each day
        current_date = start_date.date()
        while current_date <= end_date.date():
            date_str = current_date.strftime('%Y-%m-%d')
            summary = self._calculate_daily_summary(date_str)
            if summary:
                saved_summary = self.repo.upsert_daily_summary(summary)
                summaries.append(saved_summary)

            current_date += timedelta(days=1)

        return summaries

    def _calculate_daily_summary(self, date_str: str) -> DailySummary | None:
        """Calculate daily summary for a specific date."""
        date_start = datetime.strptime(date_str, '%Y-%m-%d')
        date_end = date_start + timedelta(days=1)

        summary = DailySummary(date=date_str)
        has_data = False

        # HRV metrics
        hrv_samples = self.repo.get_normalized_samples(
            metric_type=MetricType.HRV_RMSSD,
            start_date=date_start,
            end_date=date_end
        )

        if hrv_samples:
            hrv_values = [s.value for s in hrv_samples]
            summary.hrv_rmssd_avg = sum(hrv_values) / len(hrv_values)
            summary.hrv_rmssd_min = min(hrv_values)
            summary.hrv_rmssd_max = max(hrv_values)
            has_data = True

            # Calculate rolling averages
            summary.hrv_7day_avg = self._calculate_rolling_average(MetricType.HRV_RMSSD, date_str, 7)
            summary.hrv_30day_avg = self._calculate_rolling_average(MetricType.HRV_RMSSD, date_str, 30)

        # VO2 max
        vo2_samples = self.repo.get_normalized_samples(
            metric_type=MetricType.VO2MAX_MLKGMIN,
            start_date=date_start,
            end_date=date_end
        )

        if vo2_samples:
            # Take the latest reading for the day
            summary.vo2max_latest = vo2_samples[0].value
            summary.vo2max_30day_trend = self._calculate_trend(MetricType.VO2MAX_MLKGMIN, date_str, 30)
            has_data = True

        # Sleep duration
        sleep_samples = self.repo.get_normalized_samples(
            metric_type=MetricType.SLEEP_DURATION,
            start_date=date_start,
            end_date=date_end
        )

        if sleep_samples:
            total_sleep = sum(s.value for s in sleep_samples)
            summary.sleep_duration = total_sleep
            # For now, simple sleep score based on duration
            summary.sleep_score = self.sleep_calculator.calculate_sleep_score(total_sleep)
            has_data = True

        # Resting HR
        hr_samples = self.repo.get_normalized_samples(
            metric_type=MetricType.HR_RESTING,
            start_date=date_start,
            end_date=date_end
        )

        if hr_samples:
            hr_values = [s.value for s in hr_samples]
            summary.hr_resting = sum(hr_values) / len(hr_values)
            has_data = True

        return summary if has_data else None

    def _calculate_rolling_average(self, metric_type: MetricType, date_str: str, days: int) -> float | None:
        """Calculate rolling average for a metric."""
        end_date = datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=1)
        start_date = end_date - timedelta(days=days)

        samples = self.repo.get_normalized_samples(
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date
        )

        if not samples:
            return None

        return sum(s.value for s in samples) / len(samples)

    def _calculate_trend(self, metric_type: MetricType, date_str: str, days: int) -> float | None:
        """Calculate trend (change rate) for a metric."""
        summaries = self.repo.get_daily_summaries(
            end_date=date_str,
            limit=days
        )

        if len(summaries) < 2:
            return None

        # Get values for trend calculation
        values = []
        for summary in reversed(summaries):  # Oldest first
            if metric_type == MetricType.VO2MAX_MLKGMIN and summary.vo2max_latest:
                values.append(summary.vo2max_latest)
            elif metric_type == MetricType.HRV_RMSSD and summary.hrv_rmssd_avg:
                values.append(summary.hrv_rmssd_avg)

        if len(values) < 2:
            return None

        # Simple linear trend (change per day)
        first_value = values[0]
        last_value = values[-1]
        period_days = len(values) - 1

        return (last_value - first_value) / period_days if period_days > 0 else 0

    def _generate_insights(self) -> list[Insight]:
        """Generate insights from recent health data."""
        insights = []

        # HRV drop detection
        hrv_insights = self._check_hrv_trends()
        insights.extend(hrv_insights)

        # VO2 max trends
        vo2_insights = self._check_vo2_trends()
        insights.extend(vo2_insights)

        # Sleep quality alerts
        sleep_insights = self._check_sleep_quality()
        insights.extend(sleep_insights)

        # Save insights to database
        for insight in insights:
            self.repo.add_insight(insight)

        return insights

    def _check_hrv_trends(self) -> list[Insight]:
        """Check for HRV trend alerts."""
        insights = []

        # Get recent HRV trend
        trend = self.repo.get_metric_trends(MetricType.HRV_RMSSD, days=7)

        if trend["samples"] >= 5:  # Minimum samples for reliable trend
            change_pct = trend["change_pct"]
            if trend["trend"] == "declining" and change_pct < -15:
                insights.append(Insight(
                    kind="hrv_decline",
                    message=f"Your HRV has declined by {abs(change_pct):.1f}% over the past week. Consider stress management and recovery strategies.",
                    severity="warning",
                    evidence=json.dumps({
                        "change_pct": trend["change_pct"],
                        "recent_avg": trend["recent_avg"],
                        "older_avg": trend["older_avg"],
                        "samples": trend["samples"]
                    })
                ))
            elif trend["trend"] == "improving" and change_pct > 10:
                insights.append(Insight(
                    kind="hrv_improvement",
                    message=f"Great progress! Your HRV has improved by {change_pct:.1f}% over the past week.",
                    severity="info",
                    evidence=json.dumps({
                        "change_pct": trend["change_pct"],
                        "recent_avg": trend["recent_avg"],
                        "samples": trend["samples"]
                    })
                ))

        return insights

    def _check_vo2_trends(self) -> list[Insight]:
        """Check for VO2 max trend alerts."""
        insights = []

        trend = self.repo.get_metric_trends(MetricType.VO2MAX_MLKGMIN, days=30)

        if trend["samples"] >= 2:
            change_pct = trend["change_pct"]
            if trend["trend"] == "declining" and change_pct < -5:
                insights.append(Insight(
                    kind="vo2_decline",
                    message=f"Your cardiorespiratory fitness (VO₂ max) has declined by {abs(change_pct):.1f}% over the past month. Consider increasing aerobic exercise intensity.",
                    severity="warning",
                    evidence=json.dumps(trend)
                ))
            elif trend["trend"] == "improving" and change_pct > 3:
                insights.append(Insight(
                    kind="vo2_improvement",
                    message=f"Excellent! Your VO₂ max has improved by {change_pct:.1f}% this month. Your cardio training is paying off.",
                    severity="info",
                    evidence=json.dumps(trend)
                ))

        return insights

    def _check_sleep_quality(self) -> list[Insight]:
        """Check for sleep quality issues."""
        insights = []

        # Get recent sleep summaries
        summaries = self.repo.get_daily_summaries(limit=7)
        sleep_scores = [s.sleep_score for s in summaries if s.sleep_score is not None]

        if len(sleep_scores) >= 3:
            avg_sleep_score = sum(sleep_scores) / len(sleep_scores)

            if avg_sleep_score < 60:
                insights.append(Insight(
                    kind="poor_sleep",
                    message=f"Your average sleep quality score is {avg_sleep_score:.0f}/100 over the past week. Consider improving sleep hygiene and consistency.",
                    severity="warning",
                    evidence=json.dumps({
                        "avg_score": avg_sleep_score,
                        "days_analyzed": len(sleep_scores),
                        "scores": sleep_scores
                    })
                ))
            elif avg_sleep_score >= 80:
                insights.append(Insight(
                    kind="good_sleep",
                    message=f"Great sleep quality! Your average score is {avg_sleep_score:.0f}/100 this week.",
                    severity="info",
                    evidence=json.dumps({
                        "avg_score": avg_sleep_score,
                        "days_analyzed": len(sleep_scores)
                    })
                ))

        return insights


def process_health_export(xml_path: str) -> dict[str, Any]:
    """Process health export (convenience function)."""
    with next(get_db_session()) as session:
        service = HealthService(session)
        return service.process_apple_health_export(xml_path)
