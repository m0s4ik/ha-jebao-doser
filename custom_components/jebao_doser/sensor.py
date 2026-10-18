"""Sensors: schedule, daily amount, interval and last manual/scheduled dose per head."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import RestoreSensor, SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import DoserConfigEntry
from .entity import DoserEntity
from .lib import interval, schedule, schedule_enabled


async def async_setup_entry(
    hass: HomeAssistant, entry: DoserConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    c = entry.runtime_data
    entities: list[SensorEntity] = []
    for h in range(1, c.heads + 1):
        entities += [ScheduleSensor(c, "schedule", h), AmountSensor(c, "amount", h),
                     IntervalSensor(c, "interval", h), LastDoseSensor(c, "last_dose", h)]
    async_add_entities(entities)


class ScheduleSensor(DoserEntity, SensorEntity):
    """State: dose times, e.g. "17:30"; attributes: every dose with its amount."""

    _attr_translation_key = "schedule"

    @property
    def native_value(self) -> str | None:
        doses = schedule(self.coordinator.data or {}, self.head)
        return ", ".join(d["time"] for d in doses) if doses else "-"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {"doses": schedule(data, self.head), "interval_days": interval(data, self.head),
                "enabled": schedule_enabled(data, self.head)}


class AmountSensor(DoserEntity, SensorEntity):
    """Total amount of one dosing day (sum of the schedule)."""

    _attr_translation_key = "amount"
    _attr_device_class = SensorDeviceClass.VOLUME
    _attr_native_unit_of_measurement = UnitOfVolume.MILLILITERS

    @property
    def native_value(self) -> int:
        return sum(d["amount"] for d in schedule(self.coordinator.data or {}, self.head))


class IntervalSensor(DoserEntity, SensorEntity):
    """Days between dosing days (0 = every day)."""

    _attr_translation_key = "interval"
    _attr_native_unit_of_measurement = UnitOfTime.DAYS

    @property
    def native_value(self) -> int | None:
        return interval(self.coordinator.data or {}, self.head)


class LastDoseSensor(DoserEntity, RestoreSensor):
    """When the head last ran (scheduled, from the app or from the buttons)."""

    _attr_translation_key = "last_dose"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, key, head) -> None:
        super().__init__(coordinator, key, head)
        self._value: datetime | None = None
        self._duration: float | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state not in ("unknown", "unavailable"):
            self._value = dt_util.parse_datetime(last.state)
            self._duration = last.attributes.get("duration")

    def _handle_coordinator_update(self) -> None:
        if dose := self.coordinator.last_dose.get(self.head):
            self._value, self._duration = dose.start, dose.duration
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> datetime | None:
        return self._value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"duration": self._duration}
