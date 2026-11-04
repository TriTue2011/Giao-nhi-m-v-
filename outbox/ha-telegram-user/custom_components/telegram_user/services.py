"""Service khung P0: gửi tin qua module (mock ở P0, thật từ P1).

Service: telegram_user.send_message {peer, message, account?}.
Mic HA trực tiếp (P2) bắt buộc integration này mở rộng thêm (POST khối PCM
qua /m/audio/in) — không làm ở P0.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall

from . import DOMAIN, _goi


async def async_setup_services(hass: HomeAssistant, entry) -> None:
    async def _gui_tin(call: ServiceCall) -> None:
        than = {"peer": call.data["peer"], "message": call.data["message"]}
        if call.data.get("account"):
            than["account"] = call.data["account"]
        await _goi(hass, entry, "send_message", method="POST", than=than)

    hass.services.async_register(
        DOMAIN,
        "send_message",
        _gui_tin,
        schema=vol.Schema(
            {
                vol.Required("peer"): str,
                vol.Required("message"): str,
                vol.Optional("account"): str,
            }
        ),
    )
