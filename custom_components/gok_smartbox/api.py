"""Client for the GOK SmartBox cloud API."""
from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_BASE_URL, API_KEY


class GokApiError(Exception):
    """Generic API failure."""


class GokDeviceNotFound(GokApiError):
    """The device ID is unknown to the cloud."""


class GokSmartboxApi:
    """Thin async client."""

    def __init__(self, session: aiohttp.ClientSession, device_id: str) -> None:
        self._session = session
        self._device_id = device_id

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch the device record including measurement history."""
        url = f"{API_BASE_URL}/sb/mac/{self._device_id}"
        try:
            async with self._session.get(
                url, params={"code": API_KEY}, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 404:
                    raise GokDeviceNotFound(self._device_id)
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise GokApiError(str(err)) from err
