"""Manual dose buttons: run a head for the amount set in its "manual dose" number."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DoserConfigEntry
from .const import DEFAULT_MANUAL_ML
from .entity import DoserEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: DoserConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities(DoseButton(c, "dose", h) for h in range(1, c.heads + 1))


class DoseButton(DoserEntity, ButtonEntity):
    _attr_translation_key = "dose"
    _attr_icon = "mdi:water-plus"

    async def async_press(self) -> None:
        await self.coordinator.async_dose(self.head, ml=self.coordinator.manual_ml.get(self.head, DEFAULT_MANUAL_ML))
