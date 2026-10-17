"""Sensors for GOK SmartBox."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfLength,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import GokConfigEntry
from .const import DOMAIN
from .coordinator import GokSmartboxCoordinator


@dataclass(frozen=True, kw_only=True)
class GokSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _max_hv_value(data: dict[str, Any], key: str) -> float | None:
    """Largest value of `key` across the tank's height/volume calibration pairs.

    The last/largest hvPair represents the tank's total capacity.
    """
    values = [
        pair[key]
        for pair in data["tank"].get("hvPairs") or []
        if isinstance(pair.get(key), (int, float))
    ]
    return max(values) if values else None


SENSORS: tuple[GokSensorDescription, ...] = (
    GokSensorDescription(
        key="volume",
        translation_key="volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d["measurement"].get("volume"),
    ),
    GokSensorDescription(
        key="percent",
        translation_key="fill_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda d: d["measurement"].get("percent"),
    ),
    GokSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["measurement"].get("battery"),
    ),
    GokSensorDescription(
        key="height",
        translation_key="height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda d: d["measurement"].get("height"),
    ),
    GokSensorDescription(
        key="refill_capacity",
        translation_key="refill_capacity",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda d: d["measurement"].get("refillVolume"),
    ),
    GokSensorDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: dt_util.parse_datetime(d["measurement"]["timestamp"])
        if d["measurement"].get("timestamp")
        else None,
    ),
    GokSensorDescription(
        key="total_volume",
        translation_key="total_volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _max_hv_value(d, "volume"),
    ),
    GokSensorDescription(
        key="total_height",
        translation_key="total_height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda d: _max_hv_value(d, "height"),
    ),
    GokSensorDescription(
        key="filling_limit",
        translation_key="filling_limit",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["tank"].get("fillingLimit"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: GokConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(GokSensor(coordinator, d) for d in SENSORS)


class GokSensor(CoordinatorEntity[GokSmartboxCoordinator], SensorEntity):
    entity_description: GokSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: GokSmartboxCoordinator, description: GokSensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.device_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=f"SmartBox {coordinator.device_id}",
            manufacturer="GOK",
            model="SmartBox",
        )

    @property
    def native_value(self) -> float | datetime | None:
        return self.entity_description.value_fn(self.coordinator.data)
