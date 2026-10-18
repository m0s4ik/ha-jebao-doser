"""Local control of Jebao (Gizwits) aquarium dosing pumps."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import DoserCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

type DoserConfigEntry = ConfigEntry[DoserCoordinator]


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
