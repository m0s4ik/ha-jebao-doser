"""Binary sensors: dosing heads, power, alarms, connection."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import DoserConfigEntry
from .entity import DoserEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: DoserConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    c = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        ConnectionSensor(c, "connection"),
        PointSensor(c, "power", "switch", BinarySensorDeviceClass.POWER),
        PointSensor(c, "open_circuit", "OpenCircuit", BinarySensorDeviceClass.PROBLEM),
        PointSensor(c, "module_fault", "Fault_UART", BinarySensorDeviceClass.PROBLEM, EntityCategory.DIAGNOSTIC),
    ]
    entities += [
        PointSensor(c, "dosing", f"channe{h}", BinarySensorDeviceClass.RUNNING, head=h)
        for h in range(1, c.heads + 1)
    ]
    async_add_entities(entities)


class PointSensor(DoserEntity, BinarySensorEntity):
    def __init__(self, coordinator, key, point, device_class, category=None, head=None) -> None:
        super().__init__(coordinator, key, head)
        self._point = point
        self._attr_translation_key = key
        self._attr_device_class = device_class
        self._attr_entity_category = category

    @property
    def is_on(self) -> bool | None:
        return bool(self.coordinator.data.get(self._point)) if self.coordinator.data else None


class ConnectionSensor(DoserEntity, BinarySensorEntity):
    _attr_translation_key = "connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.connected
