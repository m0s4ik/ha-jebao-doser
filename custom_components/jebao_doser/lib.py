"""The jebao-doser library (installed by Home Assistant from PyPI, see manifest.json)."""

import asyncio

from jebao_doser import MAX_DOSE_SECONDS, Dose, Doser, ProtocolError, SchemaError, dosing, interval, schedule, schedule_enabled

# everything the library can raise while talking to the pump (ConnectionError is an OSError)
PUMP_ERRORS = (OSError, asyncio.IncompleteReadError, asyncio.TimeoutError, ProtocolError, SchemaError)

__all__ = ["MAX_DOSE_SECONDS", "PUMP_ERRORS", "Dose", "Doser", "ProtocolError", "SchemaError", "dosing", "interval", "schedule", "schedule_enabled"]
