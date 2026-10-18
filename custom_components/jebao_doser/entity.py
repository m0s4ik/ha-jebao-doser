"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DoserCoordinator


class DoserEntity(CoordinatorEntity[DoserCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DoserCoordinator, key: str, head: int | None = None) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self.head = head
        self._attr_unique_id = f"{entry.entry_id}_{key}" + (f"_{head}" if head else "")
        if head:
            self._attr_translation_placeholders = {"head": str(head)}
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name=entry.title, manufacturer="Jebao")

    @property
    def device_info(self) -> DeviceInfo:
        info = dict(self._attr_device_info)
        doser = self.coordinator.doser
        if doser.schema:
            info["model"] = doser.schema.product_name
        if doser.info:
            info["sw_version"] = doser.info.firmware
        return DeviceInfo(**info)

    @property
    def available(self) -> bool:
        return self.coordinator.connected and self.coordinator.data is not None
