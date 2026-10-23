"""Lampster (BLE robotlamp) voor Home Assistant."""

from __future__ import annotations

from datetime import timedelta
import logging

from bleak.exc import BleakError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL_SECONDS
from .device import LampsterDevice, LampState

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.SENSOR]

type LampsterConfigEntry = ConfigEntry[LampsterCoordinator]


class LampsterCoordinator(DataUpdateCoordinator[LampState]):
    """Haalt periodiek de lampstatus op."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device: LampsterDevice
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {device.address}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.device = device

    async def _async_update_data(self) -> LampState:
        try:
            return await self.device.async_update()
        except (BleakError, TimeoutError, OSError) as err:
            raise UpdateFailed(f"Lampster niet bereikbaar: {err}") from err


async def async_setup_entry(hass: HomeAssistant, entry: LampsterConfigEntry) -> bool:
    device = LampsterDevice(hass, entry.data[CONF_ADDRESS], entry.title)
    coordinator = LampsterCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LampsterConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.device.async_disconnect()
    return unloaded
