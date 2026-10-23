"""Temperatuursensor van de Lampster."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LampsterConfigEntry, LampsterCoordinator
from .entity import LampsterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LampsterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([LampsterTemperature(entry.runtime_data)])


class LampsterTemperature(LampsterEntity, SensorEntity):
    _attr_translation_key = "temperature"
    _attr_name = "Temperatuur"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: LampsterCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._address}_temperature"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.temperature
