"""Basisentiteit."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LampsterCoordinator
from .const import DOMAIN


class LampsterEntity(CoordinatorEntity[LampsterCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: LampsterCoordinator) -> None:
        super().__init__(coordinator)
        address = coordinator.device.address
        self._address = address
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=coordinator.device.name,
            manufacturer="Lampster",
            model="Robotlamp (BLE)",
        )
