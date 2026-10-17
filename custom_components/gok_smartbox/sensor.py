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


SENSORS: tuple[GokSensorDescription, ...] = (
    GokSensorDescription(
        key="volume",
        translation_key="volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda m: m.get("volume"),
    ),
    GokSensorDescription(
        key="percent",
        translation_key="fill_level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda m: m.get("percent"),
    ),
    GokSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: m.get("battery"),
    ),
    GokSensorDescription(
        key="height",
        translation_key="height",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda m: m.get("height"),
    ),
    GokSensorDescription(
        key="refill_volume",
        translation_key="refill_volume",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        value_fn=lambda m: m.get("refillVolume"),
    ),
    GokSensorDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda m: dt_util.parse_datetime(m["timestamp"])
        if m.get("timestamp")
        else None,
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
