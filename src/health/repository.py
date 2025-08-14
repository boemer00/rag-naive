"""Data access objects for health metrics."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from .models import DailySummary, Insight, NormalizedSample, RawSample


class HealthRepository:
    """Repository for health metrics data access."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # Raw samples
    def add_raw_sample(self, sample: RawSample) -> RawSample:
        """Add a raw sample to the database."""
        self.session.add(sample)
        self.session.commit()
        self.session.refresh(sample)
        return sample

    def add_raw_samples(self, samples: list[RawSample]) -> list[RawSample]:
        """Add multiple raw samples."""
        self.session.add_all(samples)
        self.session.commit()
        for sample in samples:
            self.session.refresh(sample)
        return samples

    def get_raw_samples(
        self,
        metric_type: str | None = None,
        provider: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000
    ) -> Sequence[RawSample]:
        """Get raw samples with filters."""
        query = self.session.query(RawSample)

        if metric_type:
            query = query.filter(RawSample.metric_type == metric_type)
        if provider:
            query = query.filter(RawSample.provider == provider)
        if start_date:
            query = query.filter(RawSample.start_time >= start_date)
        if end_date:
            query = query.filter(RawSample.start_time <= end_date)

        return query.order_by(desc(RawSample.start_time)).limit(limit).all()

    # Normalized samples
    def add_normalized_sample(self, sample: NormalizedSample) -> NormalizedSample:
        """Add a normalized sample."""
        self.session.add(sample)
        self.session.commit()
        self.session.refresh(sample)
        return sample

    def add_normalized_samples(self, samples: list[NormalizedSample]) -> list[NormalizedSample]:
        """Add multiple normalized samples."""
        self.session.add_all(samples)
        self.session.commit()
        for sample in samples:
            self.session.refresh(sample)
        return samples

    def get_normalized_samples(
        self,
        metric_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 1000
    ) -> Sequence[NormalizedSample]:
        """Get normalized samples with filters."""
        query = self.session.query(NormalizedSample)

        if metric_type:
            query = query.filter(NormalizedSample.metric_type == metric_type)
        if start_date:
            query = query.filter(NormalizedSample.start_time >= start_date)
        if end_date:
            query = query.filter(NormalizedSample.start_time <= end_date)

        return query.order_by(desc(NormalizedSample.start_time)).limit(limit).all()

    # Daily summaries
    def upsert_daily_summary(self, summary: DailySummary) -> DailySummary:
        """Insert or update daily summary."""
        existing = self.session.query(DailySummary).filter_by(date=summary.date).first()

        if existing:
            # Update existing record
            for key, value in summary.__dict__.items():
                if not key.startswith('_') and key != 'id' and value is not None:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # Insert new record
            self.session.add(summary)
            self.session.commit()
            self.session.refresh(summary)
            return summary

    def get_daily_summaries(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 365
    ) -> Sequence[DailySummary]:
        """Get daily summaries for date range."""
        query = self.session.query(DailySummary)

        if start_date:
            query = query.filter(DailySummary.date >= start_date)
        if end_date:
            query = query.filter(DailySummary.date <= end_date)

        return query.order_by(desc(DailySummary.date)).limit(limit).all()

    def get_latest_summary(self) -> DailySummary | None:
        """Get the most recent daily summary."""
        return self.session.query(DailySummary).order_by(desc(DailySummary.date)).first()

    # Insights
    def add_insight(self, insight: Insight) -> Insight:
        """Add a new insight."""
        self.session.add(insight)
        self.session.commit()
        self.session.refresh(insight)
        return insight

    def get_recent_insights(self, limit: int = 50) -> Sequence[Insight]:
        """Get recent insights."""
        return (self.session.query(Insight)
                .order_by(desc(Insight.created_at))
                .limit(limit)
                .all())

    def get_unacknowledged_insights(self) -> Sequence[Insight]:
        """Get insights that haven't been acknowledged."""
        return (self.session.query(Insight)
                .filter(not Insight.acknowledged)
                .order_by(desc(Insight.created_at))
                .all())

    def acknowledge_insight(self, insight_id: int) -> bool:
        """Mark an insight as acknowledged."""
        insight = self.session.query(Insight).filter_by(id=insight_id).first()
        if insight:
            insight.acknowledged = True
            self.session.commit()
            return True
        return False

    # Analytics helpers
    def get_metric_trends(
        self,
        metric_type: str,
        days: int = 30
    ) -> dict[str, Any]:
        """Get trend analysis for a metric."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        samples = self.get_normalized_samples(
            metric_type=metric_type,
            start_date=start_date,
            end_date=end_date
        )

        if not samples:
            return {"trend": "no_data", "change": 0, "samples": 0}

        values = [s.value for s in samples]
        recent_avg = sum(values[:len(values)//3]) / (len(values)//3) if len(values) >= 3 else values[0]
        older_avg = sum(values[len(values)//3:]) / (len(values) - len(values)//3) if len(values) >= 3 else values[-1]

        change_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0

        if abs(change_pct) < 2:
            trend = "stable"
        elif change_pct > 0:
            trend = "improving"
        else:
            trend = "declining"

        return {
            "trend": trend,
            "change_pct": change_pct,
            "recent_avg": recent_avg,
            "older_avg": older_avg,
            "samples": len(samples)
        }
