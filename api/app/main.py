from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request, Response

from app.etl import parse_precios
from app.flota import disponibilidad, lecturas_odometro
from app.proveedor import generar_csv

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

app = FastAPI(title="flota-ops API", version="0.1.0")


def _ahora() -> datetime:
    return datetime.now(ZONA)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/vehiculos/odometros")
def odometros() -> list[dict]:
    return lecturas_odometro(_ahora())


@app.get("/turnos/disponibilidad")
def turnos_disponibilidad(fecha: date) -> dict:
    if fecha < _ahora().date():
        raise HTTPException(status_code=400, detail="La fecha ya pasó")
    return {"fecha": fecha.isoformat(), "horarios": disponibilidad(fecha)}


@app.get("/proveedor/lista-precios")
def lista_precios(dia: date | None = None) -> Response:
    contenido = generar_csv(dia or _ahora().date())
    return Response(content=contenido, media_type="text/csv; charset=windows-1252")


@app.post("/etl/precios")
async def etl_precios(request: Request) -> dict:
    resultado = parse_precios(await request.body())
    return asdict(resultado)
