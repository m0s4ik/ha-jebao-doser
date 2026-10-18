"""The jebao-doser library: from PyPI when installed, else the bundled copy."""

try:
    from jebao_doser import Dose, Doser, ProtocolError, SchemaError, dosing, interval, schedule
except ImportError:  # bundled copy (vendor/), until the library is on PyPI
    from .vendor.jebao_doser import Dose, Doser, ProtocolError, SchemaError, dosing, interval, schedule

__all__ = ["Dose", "Doser", "ProtocolError", "SchemaError", "dosing", "interval", "schedule"]
