"""Holds the pump status pushed over the local connection."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_HEADS, DEFAULT_HEADS, DOMAIN
from .lib import Dose, Doser

_LOGGER = logging.getLogger(__name__)


def schema_cache(hass: HomeAssistant) -> str:
    return hass.config.path(".storage", DOMAIN)


class DoserCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """No polling: the pump pushes its full status after every change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=None)
        self.heads: int = entry.options.get(CONF_HEADS, entry.data.get(CONF_HEADS, DEFAULT_HEADS))
        self.last_dose: dict[int, Dose] = {}
        self.doser = Doser(
            entry.data[CONF_HOST],
            cache_dir=schema_cache(hass),
            on_status=self._on_status,
            on_dose=self._on_dose,
            on_connection=self._on_connection,
        )

    @property
    def connected(self) -> bool:
        return self.doser.connected

    @callback
    def _on_dose(self, dose: Dose) -> None:
        self.last_dose[dose.head] = dose

    @callback
    def _on_status(self, status: dict[str, Any]) -> None:
        self.async_set_updated_data(status)

    @callback
    def _on_connection(self, connected: bool) -> None:
        self.async_update_listeners()
