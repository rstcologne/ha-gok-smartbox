"""Data update coordinator for GOK SmartBox."""
from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import GokApiError, GokSmartboxApi
from .const import CONF_DEVICE_ID, CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN, INTERVALS

_LOGGER = logging.getLogger(__name__)


def _timestamp_key(measurement: dict[str, Any]) -> datetime:
    """Sort key for measurements: parsed timestamp, aware minimum as fallback."""
    parsed = dt_util.parse_datetime(measurement.get("timestamp") or "")
    return parsed if parsed is not None else datetime.min.replace(tzinfo=UTC)


class GokSmartboxCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the cloud and exposes the latest measurement."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.device_id: str = entry.data[CONF_DEVICE_ID]
        interval = INTERVALS[entry.data.get(CONF_INTERVAL, DEFAULT_INTERVAL)]
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{self.device_id}",
            update_interval=interval,
        )
        self.api = GokSmartboxApi(async_get_clientsession(hass), self.device_id)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_data()
        except GokApiError as err:
            raise UpdateFailed(f"Error fetching SmartBox data: {err}") from err
        measurements = data.get("measurements") or []
        if not measurements:
            raise UpdateFailed("No measurements returned")
        # Oldest -> newest; take the most recent by parsed timestamp, as string
        # comparison breaks if the API ever mixes formats (e.g. "Z" vs "+00:00").
        # Also expose the (mostly static) tank settings for config sensors.
        tank = (data.get("settings") or {}).get("tank") or {}
        return {"measurement": max(measurements, key=_timestamp_key), "tank": tank}
