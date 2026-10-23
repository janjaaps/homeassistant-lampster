"""BLE communicatie met de Lampster (verbinden per opdracht, daarna loskoppelen)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant, callback

from .const import (
    CHAR_RGB,
    CHAR_STATUS,
    CHAR_TEMP,
    CHAR_WHITE,
    IDLE_DISCONNECT_SECONDS,
    STATUS_ON_RGB,
    STATUS_ON_WHITE,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class LampState:
    """Laatst bekende toestand van de lamp."""

    status: int = 0
    warm: int = 0  # 0-100
    cool: int = 0  # 0-100
    red: int = 0  # 0-100
    green: int = 0
    blue: int = 0
    temperature: float | None = None

    @property
    def is_on(self) -> bool:
        return bool(self.status & 0x80)

    @property
    def is_rgb(self) -> bool:
        return bool(self.status & 0x20)


class LampsterDevice:
    """Een Lampster, bereikbaar via HA Bluetooth (adapter of ESPHome-proxy)."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self.hass = hass
        self.address = address
        self.name = name
        self.state = LampState()
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._idle_handle: asyncio.TimerHandle | None = None

    # -- verbinding ---------------------------------------------------------

    async def _connect(self) -> BleakClient:
        if self._client is not None and self._client.is_connected:
            return self._client
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            raise BleakNotFoundError(f"{self.name} niet gevonden via Bluetooth")
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            self.name,
            disconnected_callback=self._on_disconnect,
            max_attempts=3,
        )
        return self._client

    @callback
    def _on_disconnect(self, _client: BleakClient) -> None:
        self._client = None

    @callback
    def _schedule_idle_disconnect(self) -> None:
        if self._idle_handle:
            self._idle_handle.cancel()
        self._idle_handle = self.hass.loop.call_later(
            IDLE_DISCONNECT_SECONDS,
            lambda: self.hass.async_create_task(self.async_disconnect()),
        )

    async def async_disconnect(self) -> None:
        async with self._lock:
            if self._idle_handle:
                self._idle_handle.cancel()
                self._idle_handle = None
            client, self._client = self._client, None
            if client is not None and client.is_connected:
                try:
                    await client.disconnect()
                except BleakError:
                    pass

    async def _write(self, client: BleakClient, char: str, data: bytes) -> None:
        try:
            await client.write_gatt_char(char, data, response=True)
        except BleakError:
            await client.write_gatt_char(char, data, response=False)

    # -- lezen --------------------------------------------------------------

    async def _read_state(self, client: BleakClient) -> LampState:
        status = (await client.read_gatt_char(CHAR_STATUS))[0]
        white = await client.read_gatt_char(CHAR_WHITE)
        rgb = await client.read_gatt_char(CHAR_RGB)
        temp: float | None = self.state.temperature
        try:
            raw = await client.read_gatt_char(CHAR_TEMP)
            if len(raw) >= 2:
                temp = int.from_bytes(raw[:2], "little", signed=True) / 100.0
        except (BleakError, KeyError):
            pass
        return LampState(
            status=status,
            warm=white[0] if len(white) > 0 else 0,
            cool=white[1] if len(white) > 1 else 0,
            red=rgb[0] if len(rgb) > 0 else 0,
            green=rgb[1] if len(rgb) > 1 else 0,
            blue=rgb[2] if len(rgb) > 2 else 0,
            temperature=temp,
        )

    async def async_update(self) -> LampState:
        async with self._lock:
            client = await self._connect()
            self.state = await self._read_state(client)
            self._schedule_idle_disconnect()
            return self.state

    # -- schrijven ----------------------------------------------------------

    async def async_turn_off(self) -> LampState:
        """Zet uit met het uit-byte dat bij de HUIDIGE modus hoort."""
        async with self._lock:
            client = await self._connect()
            status = (await client.read_gatt_char(CHAR_STATUS))[0]
            if status in (STATUS_ON_WHITE, STATUS_ON_RGB):
                await self._write(client, CHAR_STATUS, bytes([status & 0x7F]))
                status &= 0x7F
            self.state = LampState(**{**self.state.__dict__, "status": status})
            self._schedule_idle_disconnect()
            return self.state

    async def async_set_white(self, warm: int, cool: int) -> LampState:
        async with self._lock:
            client = await self._connect()
            await self._write(client, CHAR_WHITE, bytes([warm, cool]))
            await self._write(client, CHAR_STATUS, bytes([STATUS_ON_WHITE]))
            self.state = LampState(
                **{**self.state.__dict__, "status": STATUS_ON_WHITE, "warm": warm, "cool": cool}
            )
            self._schedule_idle_disconnect()
            return self.state

    async def async_set_rgb(self, red: int, green: int, blue: int) -> LampState:
        async with self._lock:
            client = await self._connect()
            await self._write(client, CHAR_RGB, bytes([red, green, blue]))
            await self._write(client, CHAR_STATUS, bytes([STATUS_ON_RGB]))
            self.state = LampState(
                **{
                    **self.state.__dict__,
                    "status": STATUS_ON_RGB,
                    "red": red,
                    "green": green,
                    "blue": blue,
                }
            )
            self._schedule_idle_disconnect()
            return self.state
