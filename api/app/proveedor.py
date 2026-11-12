"""Simula el archivo diario de precios del proveedor de repuestos.

Es determinístico por fecha: el mismo día devuelve siempre los mismos bytes, y
de un día a otro cambian algunos precios y aparecen filas desprolijas
(duplicados, precios no numéricos, códigos inválidos) para ejercitar el ETL.
"""

from __future__ import annotations

import zlib
from datetime import date

# Mismo catálogo y precios base que sql/02_seed.sql.
CATALOGO = [
    ("FIL-ACE-001", "Filtro de aceite", 9500.00),
    ("FIL-AIR-002", "Filtro de aire", 8200.00),
    ("FIL-COM-003", "Filtro de combustible", 12400.00),
    ("PAS-FRE-010", "Pastillas de freno delanteras", 38500.00),
    ("PAS-FRE-011", "Pastillas de freno traseras", 29800.00),
    ("DIS-FRE-012", "Disco de freno", 64200.00),
    ("BAT-12V-020", "Batería 12V 75Ah", 185000.00),
    ("BUJ-PRE-030", "Bujía de precalentamiento", 7800.00),
    ("COR-DIS-040", "Correa de distribución", 52300.00),
    ("AMO-DEL-050", "Amortiguador delantero", 71500.00),
    ("LIQ-REF-060", "Líquido refrigerante 5 L", 13900.00),
    ("ACE-MOT-070", "Aceite de motor 15W40 5 L", 42500.00),
]


def generar_csv(dia: date) -> bytes:
    alterno = dia.day % 7 == 0
    if alterno:
        lineas = ["SKU;Detalle;Precio Lista;Moneda"]
    else:
        lineas = ["Codigo;Descripcion;Precio;Moneda"]
    for sku, descripcion, base in CATALOGO:
        precio = round(base * _factor(sku, dia), 2)
        lineas.append(f"{sku};{descripcion};{_formatear(precio, sku, dia)};ARS")

    if dia.day % 3 == 0:  # fila repetida
        lineas.append(lineas[1 + dia.day % len(CATALOGO)])
    if dia.day % 4 == 0:  # código inválido
        lineas.append("REP-XX;Repuesto sin código;1500,00;ARS")
    if dia.day % 5 == 0:  # precio no numérico
        lineas.append("BAT-12V-021;Batería 12V 60Ah;consultar;ARS")

    lineas.insert(len(lineas) // 2, "")  # línea en blanco
    return "\r\n".join(lineas).encode("cp1252")


def _factor(sku: str, dia: date) -> float:
    """Cada día cambia el precio de cerca del 60 % de los SKU (entre -3 % y +14 %)."""
    h = zlib.crc32(f"{sku}|{dia.isoformat()}".encode())
    if h % 5 < 2:
        return 1.0
    return 1 + ((h >> 3) % 1700) / 10000 - 0.03


def _formatear(precio: float, sku: str, dia: date) -> str:
    """Coma decimal; a veces con punto de miles ('9.500,00') y a veces sin ('9500,00')."""
    con_miles = zlib.crc32(f"{sku}|{dia.isoformat()}|fmt".encode()) % 2 == 0
    texto = f"{precio:,.2f}" if con_miles else f"{precio:.2f}"
    if con_miles:
        return texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return texto.replace(".", ",")
