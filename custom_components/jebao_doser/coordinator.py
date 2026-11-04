"""Holds the pump status pushed over the local connection."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from homeassistant.exceptions import HomeAssistantError

from .const import CONF_HEADS, CONF_ML_PER_MINUTE, DEFAULT_HEADS, DEFAULT_ML_PER_MINUTE, DOMAIN
from .lib import MAX_DOSE_SECONDS, PUMP_ERRORS, Dose, Doser, dosing

CONFIRM_TIMEOUT = 3
STOP_ATTEMPTS = 4
STOP_RETRY_DELAY = 1

_LOGGER = logging.getLogger(__name__)


def schema_cache(hass: HomeAssistant) -> str:
    return hass.config.path(".storage", DOMAIN)


class DoserCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """No polling: the pump pushes its full status after every change."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=None)
        self.heads: int = entry.options.get(CONF_HEADS, entry.data.get(CONF_HEADS, DEFAULT_HEADS))
        self.last_dose: dict[int, Dose] = {}
        self.ml_per_minute: float = entry.options.get(CONF_ML_PER_MINUTE, DEFAULT_ML_PER_MINUTE)
        self.manual_ml: dict[int, float] = {}
        self._dosing: set[int] = set()
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

    async def async_dose(self, head: int, ml: float | None = None, seconds: float | None = None) -> None:
        """Run a head for ``seconds``, or long enough for ``ml`` at the configured flow."""
        if not 1 <= head <= self.heads:
            raise HomeAssistantError(f"Head {head} does not exist")
        if seconds is None:
            seconds = (ml or 0) * 60.0 / self.ml_per_minute
        if not 0 < seconds <= MAX_DOSE_SECONDS:
            raise HomeAssistantError(f"Dose must last between 0 and {MAX_DOSE_SECONDS} s (asked {seconds:.1f} s)")
        if head in self._dosing:
            raise HomeAssistantError(f"Head {head} is already dosing")
        if not self.connected:
            raise HomeAssistantError("Pump not connected")
        self._dosing.add(head)
        started = asyncio.Event()
        remove = self.async_add_listener(lambda: dosing(self.data or {}, head) and started.set())
        error: Exception | None = None
        try:
            # the pump confirms by reporting the head as running: without it, stop and say so
            await self.doser.write(**{f"channe{head}": True})
            try:
                await asyncio.wait_for(started.wait(), CONFIRM_TIMEOUT)
            except TimeoutError:
                raise HomeAssistantError(f"The pump did not confirm head {head} started") from None
            await asyncio.sleep(seconds)
        except PUMP_ERRORS as err:
            error = err
            raise HomeAssistantError(f"Pump not reachable: {err}") from err
        finally:
            remove()
            # shielded: the stop must reach the pump even if the service call is cancelled
            if not await asyncio.shield(self._stop(head)):
                raise HomeAssistantError(
                    f"Could not stop head {head}: the pump may still be running, check it"
                ) from error

    async def _stop(self, head: int) -> bool:
        """Switch a head off, retrying until the pump reports it stopped. Always frees the head."""
        try:
            for attempt in range(1, STOP_ATTEMPTS + 1):
                stopped = asyncio.Event()
                remove = self.async_add_listener(lambda: not dosing(self.data or {}, head) and stopped.set())
                try:
                    await self.doser.write(**{f"channe{head}": False})
                    try:
                        await asyncio.wait_for(stopped.wait(), CONFIRM_TIMEOUT)
                        return True
                    except TimeoutError:
                        # no new status: fine if the last one already shows the head off
                        if self.data is not None and not dosing(self.data, head):
                            return True
                        _LOGGER.warning("Head %s: stop not confirmed (attempt %s/%s)", head, attempt, STOP_ATTEMPTS)
                except PUMP_ERRORS as err:
                    _LOGGER.warning("Head %s: stop failed (attempt %s/%s): %s", head, attempt, STOP_ATTEMPTS, err)
                finally:
                    remove()
                if attempt < STOP_ATTEMPTS:
                    await asyncio.sleep(STOP_RETRY_DELAY)
            _LOGGER.error("Could not stop head %s after %s attempts: the pump may still be running", head, STOP_ATTEMPTS)
            return False
        finally:
            self._dosing.discard(head)

    async def async_clear_schedule(self, head: int) -> None:
        """Delete the pump's own schedule of a head and switch it off (as in the vendor app)."""
        if not 1 <= head <= self.heads:
            raise HomeAssistantError(f"Head {head} does not exist")
        try:
            await self.doser.clear_schedule(head)
        except PUMP_ERRORS as err:
            raise HomeAssistantError(f"Pump not reachable: {err}") from err
