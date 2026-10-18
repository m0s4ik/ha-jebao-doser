"""Amount of the manual dose of each head (ml), remembered across restarts."""

from __future__ import annotations

from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import EntityCategory, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DoserConfigEntry
from .const import DEFAULT_MANUAL_ML, MAX_MANUAL_ML
from .entity import DoserEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: DoserConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities(ManualDose(c, "manual_dose", h) for h in range(1, c.heads + 1))


class ManualDose(DoserEntity, RestoreNumber):
    _attr_translation_key = "manual_dose"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0.5
    _attr_native_max_value = MAX_MANUAL_ML
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfVolume.MILLILITERS
    _attr_mode = NumberMode.BOX

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_number_data()
        value = last.native_value if last and last.native_value else DEFAULT_MANUAL_ML
        self.coordinator.manual_ml[self.head] = value

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float:
        return self.coordinator.manual_ml.get(self.head, DEFAULT_MANUAL_ML)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.manual_ml[self.head] = value
        self.async_write_ha_state()
