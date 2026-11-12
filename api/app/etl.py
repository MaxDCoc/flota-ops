"""Limpieza y validación de la lista de precios que manda el proveedor.

El archivo llega desprolijo: separador y codificación variables, coma decimal,
filas repetidas o inválidas. Cada línea de entrada termina en `limpias` o en
`rechazadas` (con el motivo), así que nunca se pierde información en silencio.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

# Nombres de columna aceptados, ya normalizados (minúsculas, sin tildes).
ALIAS = {
    "sku": {"sku", "codigo", "cod", "cod_articulo", "articulo"},
    "descripcion": {"descripcion", "detalle", "producto"},
    "precio": {"precio", "precio_lista", "importe", "precio_unitario"},
    "moneda": {"moneda", "divisa"},
    "proveedor": {"proveedor", "marca"},
}
REQUERIDAS = ("sku", "descripcion", "precio")
MONEDAS = {"ARS", "USD"}
SKU_VALIDO = re.compile(r"^[A-Z]{3}-[A-Z0-9]{3}-\d{3}$")
PRECIO_MAXIMO = 10_000_000
PROVEEDOR_POR_DEFECTO = "Repuestos Muestra S.A."


@dataclass
class EtlResult:
    lote_id: str
    limpias: list[dict] = field(default_factory=list)
    rechazadas: list[dict] = field(default_factory=list)
    resumen: dict = field(default_factory=dict)


def decode_bytes(raw: bytes) -> str:
    """Decodifica UTF-8 (con o sin BOM) y, si no es válido, Windows-1252."""
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def parse_precio(valor: str) -> float | None:
    """Convierte '9.500,50', '9500,5', '$ 1.250' o '1,234.56' en número.

    Una sola coma o un solo punto seguidos de exactamente tres dígitos se
    interpretan como separador de miles.
    """
    s = re.sub(r"[^\d.,-]", "", valor or "")
    if not re.search(r"\d", s):
        return None
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    elif "." in s and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_precios(raw: bytes, lote_id: str | None = None) -> EtlResult:
    result = EtlResult(lote_id=lote_id or _nuevo_lote())
    texto = decode_bytes(raw)
    if not texto.strip():
        return _cerrar(result, 0, "archivo vacío")

    delimitador = _detectar_delimitador(texto)
    lector = csv.reader(io.StringIO(texto), delimiter=delimitador)
    filas = [(lector.line_num, celdas) for celdas in lector]
    filas = [(n, celdas) for n, celdas in filas if any(c.strip() for c in celdas)]

    columnas = _mapear_columnas(filas[0][1])
    faltan = [c for c in REQUERIDAS if c not in columnas]
    if faltan:
        return _cerrar(result, filas[0][0], f"faltan columnas: {', '.join(faltan)}")

    validas: list[dict] = []
    leidas = 0
    for linea, celdas in filas[1:]:
        leidas += 1
        contenido = delimitador.join(celdas)
        if len(celdas) <= max(columnas.values()):
            _rechazar(result, linea, "columnas incompletas", contenido)
            continue
        fila = {nombre: celdas[i].strip() for nombre, i in columnas.items()}
        error, limpia = _validar_fila(fila)
        if error:
            _rechazar(result, linea, error, contenido)
        else:
            validas.append({**limpia, "linea_origen": linea, "contenido_origen": contenido})

    if validas:
        df = pd.DataFrame(validas)
        repetida = df.duplicated(subset="sku", keep="last")
        for fila in df[repetida].itertuples():
            _rechazar(
                result,
                int(fila.linea_origen),
                "SKU duplicado (se conserva la última línea)",
                fila.contenido_origen,
            )
        for fila in df[~repetida].itertuples():
            result.limpias.append(
                {
                    "sku": fila.sku,
                    "descripcion": fila.descripcion,
                    "proveedor": fila.proveedor,
                    "precio": float(fila.precio),
                    "moneda": fila.moneda,
                }
            )

    result.rechazadas.sort(key=lambda r: r["linea"])
    result.resumen = {
        "leidas": leidas,
        "limpias": len(result.limpias),
        "rechazadas": len(result.rechazadas),
        "duplicadas": sum("duplicado" in r["motivo"] for r in result.rechazadas),
    }
    return result


def _validar_fila(fila: dict) -> tuple[str | None, dict]:
    sku = re.sub(r"[\s_]+", "-", fila["sku"].strip()).upper()
    if not SKU_VALIDO.match(sku):
        return f"SKU inválido: {fila['sku']!r}", {}
    descripcion = re.sub(r"\s+", " ", fila["descripcion"]).strip()
    if not descripcion:
        return "descripción vacía", {}
    precio = parse_precio(fila["precio"])
    if precio is None:
        return f"precio inválido: {fila['precio']!r}", {}
    if precio <= 0:
        return "precio no positivo", {}
    if precio > PRECIO_MAXIMO:
        return "precio fuera de rango", {}
    moneda = (fila.get("moneda") or "ARS").upper()
    if moneda not in MONEDAS:
        return f"moneda no soportada: {moneda}", {}
    return None, {
        "sku": sku,
        "descripcion": descripcion,
        "proveedor": fila.get("proveedor") or PROVEEDOR_POR_DEFECTO,
        "precio": round(precio, 2),
        "moneda": moneda,
    }


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def _mapear_columnas(encabezado: list[str]) -> dict[str, int]:
    columnas: dict[str, int] = {}
    for i, titulo in enumerate(encabezado):
        nombre = _normalizar(titulo)
        for canonico, alias in ALIAS.items():
            if nombre in alias and canonico not in columnas:
                columnas[canonico] = i
    return columnas


def _detectar_delimitador(texto: str) -> str:
    primera = next(linea for linea in texto.splitlines() if linea.strip())
    cuentas = {d: primera.count(d) for d in (";", ",", "\t", "|")}
    delimitador = max(cuentas, key=cuentas.get)
    return delimitador if cuentas[delimitador] else ";"


def _nuevo_lote() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]


def _rechazar(result: EtlResult, linea: int, motivo: str, contenido: str) -> None:
    result.rechazadas.append({"linea": linea, "motivo": motivo, "contenido": contenido})


def _cerrar(result: EtlResult, linea: int, motivo: str) -> EtlResult:
    """Rechazo de archivo completo: no hay líneas para procesar."""
    _rechazar(result, linea, motivo, "")
    result.resumen = {"leidas": 0, "limpias": 0, "rechazadas": 1, "duplicadas": 0}
    return result
