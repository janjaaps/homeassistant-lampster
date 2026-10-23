"""Lampster als lichtentiteit: wit (warm/koud) of RGB."""

from __future__ import annotations

from typing import Any

from bleak.exc import BleakError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LampsterConfigEntry, LampsterCoordinator
from .const import MAX_KELVIN, MIN_KELVIN
from .entity import LampsterEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: LampsterConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([LampsterLight(entry.runtime_data)])


def _white_from_kelvin(kelvin: int, brightness: int) -> tuple[int, int]:
    """(kelvin, helderheid 0-255) -> (warm %, koud %); de sterkste kant krijgt de volle helderheid."""
    c = (min(max(kelvin, MIN_KELVIN), MAX_KELVIN) - MIN_KELVIN) / (MAX_KELVIN - MIN_KELVIN)
    b = brightness / 255 * 100
    warm = min(1.0, 2 * (1 - c)) * b
    cool = min(1.0, 2 * c) * b
    warm_i, cool_i = round(warm), round(cool)
    if brightness > 0 and warm_i == 0 and cool_i == 0:
        if warm >= cool:
            warm_i = 1
        else:
            cool_i = 1
    return warm_i, cool_i


def _kelvin_from_white(warm: int, cool: int) -> tuple[int, int]:
    """(warm %, koud %) -> (kelvin, helderheid 0-255)."""
    peak = max(warm, cool)
    if peak == 0:
        return 4000, 0
    w, c = warm / peak, cool / peak
    frac = 1 - w / 2 if c >= 1 else c / 2
    return round(MIN_KELVIN + frac * (MAX_KELVIN - MIN_KELVIN)), round(peak / 100 * 255)


class LampsterLight(LampsterEntity, LightEntity):
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.RGB}
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    def __init__(self, coordinator: LampsterCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._address}_light"

    @property
    def _state(self):
        return self.coordinator.data

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        return self._state.is_on

    @property
    def color_mode(self) -> ColorMode:
        return ColorMode.RGB if self._state.is_rgb else ColorMode.COLOR_TEMP

    @property
    def brightness(self) -> int | None:
        s = self._state
        if s.is_rgb:
            peak = max(s.red, s.green, s.blue)
        else:
            peak = max(s.warm, s.cool)
        return max(1, round(peak / 100 * 255)) if s.is_on else None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        s = self._state
        peak = max(s.red, s.green, s.blue)
        if peak == 0:
            return (255, 255, 255)
        return (
            round(s.red / peak * 255),
            round(s.green / peak * 255),
            round(s.blue / peak * 255),
        )

    @property
    def color_temp_kelvin(self) -> int | None:
        s = self._state
        return _kelvin_from_white(s.warm, s.cool)[0]

    async def async_turn_on(self, **kwargs: Any) -> None:
        s = self._state
        if ATTR_RGB_COLOR in kwargs:
            rgb_mode = True
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            rgb_mode = False
        else:
            rgb_mode = s.is_rgb

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
        else:
            brightness = self.brightness or 255

        try:
            if rgb_mode:
                r, g, b = kwargs.get(ATTR_RGB_COLOR) or self.rgb_color
                scale = brightness / 255 * 100 / 255
                vals = [round(v * scale) for v in (r, g, b)]
                if brightness > 0 and not any(vals):
                    vals[vals.index(max(vals))] = 1
                new = await self.coordinator.device.async_set_rgb(*vals)
            else:
                kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN) or self.color_temp_kelvin
                warm, cool = _white_from_kelvin(kelvin, brightness)
                new = await self.coordinator.device.async_set_white(warm, cool)
        except (BleakError, TimeoutError, OSError) as err:
            raise HomeAssistantError(f"Lampster aansturen mislukt: {err}") from err
        self.coordinator.async_set_updated_data(new)

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            new = await self.coordinator.device.async_turn_off()
        except (BleakError, TimeoutError, OSError) as err:
            raise HomeAssistantError(f"Lampster uitzetten mislukt: {err}") from err
        self.coordinator.async_set_updated_data(new)
