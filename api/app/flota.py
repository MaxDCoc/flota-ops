"""Simula el sistema de gestión del taller: lecturas de odómetro y agenda de turnos."""

from __future__ import annotations

import zlib
from datetime import date, datetime

# Mismos vehículos y kilometraje inicial que sql/02_seed.sql.
KM_BASE = {
    "AA101BB": 58200,
    "AA102BB": 71350,
    "AA103BB": 34100,
    "AC201DD": 142900,
    "AC202DD": 168000,
    "AC203DD": 41200,
    "AD301EE": 62000,
    "AD302EE": 59800,
    "AD303EE": 18900,
    "AE401FF": 95500,
    "AE402FF": 47800,
    "AF501GG": 120300,
    "AF502GG": 99500,
    "AA104BB": 12100,
}
FECHA_BASE = date(2026, 11, 12)
HORARIOS = [f"{hora:02d}:00" for hora in range(8, 17)]


def lecturas_odometro(ahora: datetime) -> list[dict]:
    """Kilometraje simulado: avanza un poco por día y por patente, y se reinicia cada 30 días."""
    dias = max((ahora.date() - FECHA_BASE).days, 0) % 30
    fraccion_del_dia = (ahora.hour * 60 + ahora.minute) / 1440
    lecturas = []
    for patente, base in KM_BASE.items():
        km_por_dia = 40 + zlib.crc32(patente.encode()) % 80
        km = base + int(km_por_dia * (dias + fraccion_del_dia))
        lecturas.append({"patente": patente, "km": km})
    return lecturas


def disponibilidad(fecha: date) -> list[str]:
    """Horarios libres: lunes a viernes de 8 a 16, sábados de 9 a 12, domingos cerrado."""
    if fecha.weekday() == 6:
        return []
    horarios = HORARIOS if fecha.weekday() < 5 else HORARIOS[1:5]
    return [h for h in horarios if zlib.crc32(f"{fecha.isoformat()}|{h}".encode()) % 4 != 0]
