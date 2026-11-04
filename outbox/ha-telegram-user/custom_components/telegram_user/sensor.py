"""Sensor khung P0: số tài khoản / số tài khoản online từ health (poll).

P1 bổ sung sensor cuộc gọi đang chạy + event entity khi module có dữ liệu thật.
"""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN, _goi


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            TelegramUserSensor(hass, entry, "accounts_total", "Tài khoản Telegram"),
            TelegramUserSensor(hass, entry, "accounts_online", "Tài khoản Telegram online"),
        ],
        update_before_add=True,
    )


class TelegramUserSensor(SensorEntity):
    _attr_should_poll = True

    def __init__(self, hass, entry, khoa, ten):
        self._hass = hass
        self._entry = entry
        self._khoa = khoa
        self._attr_name = ten
        self._attr_unique_id = f"{entry.entry_id}_{khoa}"
        self._attr_native_value = None

    async def async_update(self) -> None:
        try:
            health = await _goi(self._hass, self._entry, "health")
        except Exception:
            self._attr_available = False
            return
        self._attr_available = True
        self._attr_native_value = health.get(self._khoa)
