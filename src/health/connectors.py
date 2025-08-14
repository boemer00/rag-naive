"""Device connector interfaces for various health platforms."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .models import DeviceProvider, RawSample


class DeviceConnector(ABC):
    """Base interface for device connectors."""

    def __init__(self, provider: DeviceProvider) -> None:
        self.provider = provider

    @abstractmethod
    def get_oauth_authorize_url(self, redirect_uri: str, scopes: list[str]) -> str:
        """Get OAuth authorization URL."""
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        pass

    @abstractmethod
    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token."""
        pass

    @abstractmethod
    def fetch_metrics(
        self,
        access_token: str,
        metric_types: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> list[RawSample]:
        """Fetch metrics from device API."""
        pass

    @abstractmethod
    def handle_webhook(self, payload: dict[str, Any]) -> list[RawSample]:
        """Handle incoming webhook data."""
        pass


class AppleHealthConnector(DeviceConnector):
    """Apple Health connector (file-based for now)."""

    def __init__(self) -> None:
        super().__init__(DeviceProvider.APPLE_HEALTH)

    def get_oauth_authorize_url(self, redirect_uri: str, scopes: list[str]) -> str:
        """Apple Health uses HealthKit, no OAuth needed for XML exports."""
        raise NotImplementedError("Apple Health uses XML export, not OAuth")

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Not applicable for Apple Health."""
        raise NotImplementedError("Apple Health uses XML export, not OAuth")

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Not applicable for Apple Health."""
        raise NotImplementedError("Apple Health uses XML export, not OAuth")

    def fetch_metrics(
        self,
        access_token: str,
        metric_types: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> list[RawSample]:
        """Not applicable for Apple Health (use ETL pipeline instead)."""
        raise NotImplementedError("Use AppleHealthETL for processing XML files")

    def handle_webhook(self, payload: dict[str, Any]) -> list[RawSample]:
        """Not applicable for Apple Health."""
        raise NotImplementedError("Apple Health doesn't support webhooks")


class GarminConnector(DeviceConnector):
    """Garmin Connect IQ connector (stub implementation)."""

    def __init__(self) -> None:
        super().__init__(DeviceProvider.GARMIN)
        self.base_url = "https://connect.garmin.com"

    def get_oauth_authorize_url(self, redirect_uri: str, scopes: list[str]) -> str:
        """Get Garmin OAuth URL (stub)."""
        # TODO: Implement Garmin OAuth 1.0a
        return f"{self.base_url}/oauth/authorize?redirect_uri={redirect_uri}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange code for Garmin token (stub)."""
        # TODO: Implement Garmin token exchange
        return {"access_token": "stub", "token_secret": "stub"}

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh Garmin token (stub)."""
        # TODO: Implement token refresh
        return {"access_token": "stub", "token_secret": "stub"}

    def fetch_metrics(
        self,
        access_token: str,
        metric_types: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> list[RawSample]:
        """Fetch Garmin metrics (stub)."""
        # TODO: Implement Garmin API calls
        return []

    def handle_webhook(self, payload: dict[str, Any]) -> list[RawSample]:
        """Handle Garmin webhook (stub)."""
        # TODO: Implement webhook handling
        return []


class OuraConnector(DeviceConnector):
    """Oura Ring connector (stub implementation)."""

    def __init__(self) -> None:
        super().__init__(DeviceProvider.OURA)
        self.base_url = "https://api.ouraring.com"

    def get_oauth_authorize_url(self, redirect_uri: str, scopes: list[str]) -> str:
        """Get Oura OAuth URL (stub)."""
        # TODO: Implement Oura OAuth
        return f"{self.base_url}/oauth/authorize?redirect_uri={redirect_uri}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange code for Oura token (stub)."""
        # TODO: Implement Oura token exchange
        return {"access_token": "stub", "refresh_token": "stub"}

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh Oura token (stub)."""
        # TODO: Implement token refresh
        return {"access_token": "stub", "refresh_token": "stub"}

    def fetch_metrics(
        self,
        access_token: str,
        metric_types: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> list[RawSample]:
        """Fetch Oura metrics (stub)."""
        # TODO: Implement Oura API calls for HRV, sleep, etc.
        return []

    def handle_webhook(self, payload: dict[str, Any]) -> list[RawSample]:
        """Handle Oura webhook (stub)."""
        # TODO: Implement webhook handling
        return []


class WhoopConnector(DeviceConnector):
    """Whoop connector (stub implementation)."""

    def __init__(self) -> None:
        super().__init__(DeviceProvider.WHOOP)
        self.base_url = "https://api.prod.whoop.com"

    def get_oauth_authorize_url(self, redirect_uri: str, scopes: list[str]) -> str:
        """Get Whoop OAuth URL (stub)."""
        # TODO: Implement Whoop OAuth
        return f"{self.base_url}/oauth/authorize?redirect_uri={redirect_uri}"

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange code for Whoop token (stub)."""
        # TODO: Implement Whoop token exchange
        return {"access_token": "stub", "refresh_token": "stub"}

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh Whoop token (stub)."""
        # TODO: Implement token refresh
        return {"access_token": "stub", "refresh_token": "stub"}

    def fetch_metrics(
        self,
        access_token: str,
        metric_types: list[str],
        start_date: datetime,
        end_date: datetime
    ) -> list[RawSample]:
        """Fetch Whoop metrics (stub)."""
        # TODO: Implement Whoop API calls for HRV, sleep, recovery, etc.
        return []

    def handle_webhook(self, payload: dict[str, Any]) -> list[RawSample]:
        """Handle Whoop webhook (stub)."""
        # TODO: Implement webhook handling
        return []


def get_connector(provider: DeviceProvider) -> DeviceConnector:
    """Factory function to get device connector."""
    connectors = {
        DeviceProvider.APPLE_HEALTH: AppleHealthConnector,
        DeviceProvider.GARMIN: GarminConnector,
        DeviceProvider.OURA: OuraConnector,
        DeviceProvider.WHOOP: WhoopConnector,
    }

    connector_class = connectors.get(provider)
    if not connector_class:
        raise ValueError(f"Unsupported provider: {provider}")

    return connector_class()
