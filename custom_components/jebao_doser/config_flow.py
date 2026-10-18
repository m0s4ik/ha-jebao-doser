"""Config flow: the pump's IP is enough, it hands out its own passcode."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import callback

from .const import CONF_HEADS, CONF_ML_PER_MINUTE, DEFAULT_HEADS, DEFAULT_ML_PER_MINUTE, DOMAIN, MAX_HEADS
from .coordinator import schema_cache
from .lib import Doser, ProtocolError, SchemaError

HEADS = vol.All(vol.Coerce(int), vol.Range(min=1, max=MAX_HEADS))


class DoserConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._heads = DEFAULT_HEADS
        self._model: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            doser = Doser(host, cache_dir=schema_cache(self.hass))
            try:
                await doser.read()
            except SchemaError:
                errors["base"] = "no_schema"
            except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError, ProtocolError):
                errors["base"] = "cannot_connect"
            else:
                self._host = host
                self._heads = doser.schema.heads or DEFAULT_HEADS
                self._model = doser.schema.product_name
                return await self.async_step_details()
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_HOST): str}), errors=errors
        )

    async def async_step_details(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["name"], data={CONF_HOST: self._host, CONF_HEADS: user_input[CONF_HEADS]}
            )
        return self.async_show_form(
            step_id="details",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default="Jebao Doser"): str,
                    vol.Required(CONF_HEADS, default=self._heads): HEADS,
                }
            ),
            description_placeholders={"model": self._model or "?"},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DoserOptionsFlow()


class DoserOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        o, d = self.config_entry.options, self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HEADS, default=o.get(CONF_HEADS, d.get(CONF_HEADS, DEFAULT_HEADS))): HEADS,
                    vol.Required(CONF_ML_PER_MINUTE, default=o.get(CONF_ML_PER_MINUTE, DEFAULT_ML_PER_MINUTE)): vol.All(
                        vol.Coerce(float), vol.Range(min=1, max=500)
                    ),
                }
            ),
        )
