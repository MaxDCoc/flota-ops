import pytest

from app.etl import parse_precio, parse_precios

ENCABEZADO = "Codigo;Descripcion;Precio;Moneda\r\n"


def csv_bytes(*lineas: str, codificacion: str = "cp1252") -> bytes:
    return (ENCABEZADO + "\r\n".join(lineas)).encode(codificacion)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("9.500,00", 9500.0),
        ("9500,5", 9500.5),
        ("$ 1.250", 1250.0),
        ("12.34", 12.34),
        ("1,234.56", 1234.56),
        ("consultar", None),
        ("", None),
    ],
)
def test_parse_precio(texto, esperado):
    assert parse_precio(texto) == esperado


def test_coma_decimal():
    r = parse_precios(csv_bytes("FIL-ACE-001;Filtro de aceite;9.500,50;ARS"))
    assert r.limpias[0]["precio"] == 9500.5


def test_latin1():
    r = parse_precios(csv_bytes("BAT-12V-020;Batería 12V 75Ah;185000,00;ARS"))
    assert r.limpias[0]["descripcion"] == "Batería 12V 75Ah"


def test_duplicados_se_descartan():
    r = parse_precios(
        csv_bytes(
            "FIL-ACE-001;Filtro de aceite;9000,00;ARS",
            "FIL-ACE-001;Filtro de aceite;9500,00;ARS",
        )
    )
    assert len(r.limpias) == 1
    assert r.limpias[0]["precio"] == 9500.0
    assert r.resumen["duplicadas"] == 1
    assert r.rechazadas[0]["linea"] == 2


def test_precio_invalido_se_rechaza():
    r = parse_precios(csv_bytes("FIL-ACE-001;Filtro de aceite;consultar;ARS"))
    assert r.limpias == []
    assert r.rechazadas[0]["linea"] == 2
    assert r.rechazadas[0]["motivo"].startswith("precio inválido")


def test_precio_no_positivo_se_rechaza():
    r = parse_precios(csv_bytes("FIL-ACE-001;Filtro de aceite;0;ARS"))
    assert r.rechazadas[0]["motivo"] == "precio no positivo"


def test_sku_se_normaliza():
    r = parse_precios(csv_bytes("fil ace 001;Filtro de aceite;9500,00;ARS"))
    assert r.limpias[0]["sku"] == "FIL-ACE-001"


def test_sku_invalido_se_rechaza():
    r = parse_precios(csv_bytes("REP-XX;Repuesto;1500,00;ARS"))
    assert r.rechazadas[0]["motivo"].startswith("SKU inválido")


def test_archivo_vacio():
    r = parse_precios(b"")
    assert r.limpias == []
    assert r.resumen["leidas"] == 0
    assert r.rechazadas[0]["motivo"] == "archivo vacío"


def test_encabezados_distintos():
    raw = "SKU;Detalle;Precio Lista\r\nFIL-ACE-001;Filtro de aceite;9500,00".encode("cp1252")
    r = parse_precios(raw)
    assert r.limpias[0]["moneda"] == "ARS"
    assert r.limpias[0]["precio"] == 9500.0


def test_faltan_columnas():
    r = parse_precios(b"Codigo;Descripcion\r\nFIL-ACE-001;Filtro de aceite")
    assert r.limpias == []
    assert r.rechazadas[0]["motivo"] == "faltan columnas: precio"


def test_cada_linea_se_contabiliza():
    r = parse_precios(
        csv_bytes(
            "FIL-ACE-001;Filtro de aceite;9500,00;ARS",
            "",
            "FIL-ACE-001;Filtro de aceite;9500,00;ARS",
            "REP-XX;Repuesto;1500,00;ARS",
            "BAT-12V-021;Batería;consultar;ARS",
            "FIL-AIR-002;Filtro de aire;8200,00;ARS",
        )
    )
    assert r.resumen["leidas"] == 5
    assert r.resumen["limpias"] + r.resumen["rechazadas"] == r.resumen["leidas"]


def test_delimitador_coma():
    r = parse_precios(b"sku,descripcion,precio\r\nFIL-ACE-001,Filtro de aceite,9500.00")
    assert r.limpias[0]["precio"] == 9500.0
