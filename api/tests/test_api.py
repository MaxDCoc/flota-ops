import re
from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.proveedor import generar_csv

client = TestClient(app)


def proximo_lunes() -> date:
    hoy = date.today()
    return hoy + timedelta(days=(7 - hoy.weekday()) % 7 or 7)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_odometros():
    lecturas = client.get("/vehiculos/odometros").json()
    assert len(lecturas) == 14
    assert all({"patente", "km"} <= set(item) for item in lecturas)


def test_disponibilidad_formato():
    r = client.get("/turnos/disponibilidad", params={"fecha": proximo_lunes().isoformat()})
    assert r.status_code == 200
    horarios = r.json()["horarios"]
    assert horarios
    assert all(re.fullmatch(r"\d{2}:00", h) for h in horarios)


def test_disponibilidad_domingo_sin_horarios():
    domingo = proximo_lunes() + timedelta(days=6)
    r = client.get("/turnos/disponibilidad", params={"fecha": domingo.isoformat()})
    assert r.json()["horarios"] == []


def test_disponibilidad_fecha_pasada_es_400():
    ayer = date.today() - timedelta(days=1)
    r = client.get("/turnos/disponibilidad", params={"fecha": ayer.isoformat()})
    assert r.status_code == 400


def test_disponibilidad_fecha_invalida_es_422():
    assert client.get("/turnos/disponibilidad", params={"fecha": "mañana"}).status_code == 422


def test_lista_precios_es_cp1252():
    r = client.get("/proveedor/lista-precios", params={"dia": "2026-11-12"})
    assert "windows-1252" in r.headers["content-type"]
    assert "Batería" in r.content.decode("cp1252")


def test_lista_precios_es_determinista_por_dia():
    assert generar_csv(date(2026, 11, 12)) == generar_csv(date(2026, 11, 12))
    assert generar_csv(date(2026, 11, 12)) != generar_csv(date(2026, 11, 13))


def test_etl_endpoint_devuelve_resumen():
    archivo = client.get("/proveedor/lista-precios", params={"dia": "2026-11-12"}).content
    r = client.post("/etl/precios", content=archivo)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["lote_id"]
    resumen = cuerpo["resumen"]
    assert resumen["limpias"] == len(cuerpo["limpias"])
    assert resumen["limpias"] + resumen["rechazadas"] == resumen["leidas"]
