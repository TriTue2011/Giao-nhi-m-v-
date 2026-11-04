"""Config flow khung P0: nhập gốc w2a + khoá khách, kiểm health.

Lỗi: cannot_connect (không tới được w2a), invalid_auth (khoá sai/thiếu phạm
vi tich_hop@telegram-user). Đăng nhập tài khoản Telegram KHÔNG làm ở đây —
chỉ ở tab module trên w2a (P1).
"""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries

from . import DOMAIN


class TelegramUserConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            goc = user_input["base_url"].rstrip("/")
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{goc}/m/telegram-user/api/health",
                        headers={"Authorization": f"Bearer {user_input['guest_key']}"},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status in (401, 403):
                            errors["base"] = "invalid_auth"
                        elif resp.status != 200:
                            errors["base"] = "cannot_connect"
                        else:
                            return self.async_create_entry(
                                title="Telegram (tài khoản)",
                                data=user_input,
                            )
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
        schema = vol.Schema(
            {
                vol.Required("base_url"): str,
                vol.Required("guest_key"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
