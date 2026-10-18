"""Local control of Jebao (Gizwits) aquarium dosing pumps."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import DoserCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NUMBER, Platform.SENSOR]

type DoserConfigEntry = ConfigEntry[DoserCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
DOSE_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry_id"): cv.string,
        vol.Required("head"): vol.All(vol.Coerce(int), vol.Range(min=1, max=8)),
        vol.Exclusive("ml", "amount"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=100)),
        vol.Exclusive("seconds", "amount"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=120)),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def dose(call: ServiceCall) -> None:
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if entry is None or entry.domain != DOMAIN or not hasattr(entry, "runtime_data"):
            raise ServiceValidationError("Unknown or not loaded Jebao doser")
        if "ml" not in call.data and "seconds" not in call.data:
            raise ServiceValidationError("Give either ml or seconds")
        await entry.runtime_data.async_dose(call.data["head"], call.data.get("ml"), call.data.get("seconds"))

    hass.services.async_register(DOMAIN, "dose", dose, schema=DOSE_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: DoserConfigEntry) -> bool:
    coordinator = DoserCoordinator(hass, entry)
    entry.runtime_data = coordinator
    coordinator.doser.start()
    entry.async_on_unload(entry.add_update_listener(_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: DoserConfigEntry) -> bool:
    await entry.runtime_data.doser.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _reload(hass: HomeAssistant, entry: DoserConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
