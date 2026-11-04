"""Khung integration mỏng telegram_user (P0): chỉ cầu nối sang module w2a.

Không chứa MTProto/session/state machine — mọi logic nằm trong module
telegram-user trên web2api. Đường gọi: /m/telegram-user/api/... bằng khoá
khách do lõi w2a cấp (phạm vi tich_hop@telegram-user), chỉ LAN.
"""

from __future__ import annotations

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "telegram_user"
PLATFORMS = ["sensor"]


async def _goi(hass: HomeAssistant, entry: ConfigEntry, duong: str, method="GET", than=None):
    """Gọi đường /m của module (khung P0: chưa có retry/timeout tinh chỉnh)."""
    goc = entry.data["base_url"].rstrip("/")
    headers = {"Authorization": f"Bearer {entry.data['guest_key']}"}
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method, f"{goc}/m/telegram-user/api/{duong}", json=than, headers=headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Kiểm tra health rồi nạp sensor. Lỗi health → entry lỗi, không retry mù."""
    await _goi(hass, entry, "health")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
