"""Chequeos estáticos de los workflows de n8n.

Verifica que cada JSON sea válido, que las conexiones apunten a nodos que
existen, que todos los flujos (salvo el de errores) tengan asignado el flujo
de errores, que las credenciales referenciadas existan y que no haya secretos
escritos dentro de los parámetros.

Uso: python scripts/check_workflows.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ID_FLUJO_ERRORES = "flota-99-errores"
CLAVE_SECRETA = re.compile(r"(password|passwd|api_?key|token|secret)", re.IGNORECASE)
DISPARADORES = (
    "manualTrigger",
    "scheduleTrigger",
    "webhook",
    "errorTrigger",
)


def credenciales_conocidas() -> set[str]:
    plantilla = json.loads((RAIZ / "n8n" / "credentials.template.json").read_text("utf-8"))
    return {c["id"] for c in plantilla}


def claves_con_secretos(valor, ruta="") -> list[str]:
    hallazgos = []
    if isinstance(valor, dict):
        for clave, contenido in valor.items():
            subruta = f"{ruta}.{clave}" if ruta else clave
            es_texto_literal = isinstance(contenido, str) and contenido and not contenido.startswith("=")
            if CLAVE_SECRETA.search(clave) and es_texto_literal:
                hallazgos.append(subruta)
            hallazgos += claves_con_secretos(contenido, subruta)
    elif isinstance(valor, list):
        for i, contenido in enumerate(valor):
            hallazgos += claves_con_secretos(contenido, f"{ruta}[{i}]")
    return hallazgos


def revisar(ruta: Path, credenciales: set[str]) -> list[str]:
    errores = []
    try:
        flujo = json.loads(ruta.read_text("utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON inválido: {e}"]

    for clave in ("id", "name", "nodes", "connections"):
        if clave not in flujo:
            errores.append(f"falta la clave '{clave}'")
    if errores:
        return errores

    nombres = [n["name"] for n in flujo["nodes"]]
    if len(nombres) != len(set(nombres)):
        errores.append("hay nodos con nombre repetido")

    for origen, salidas in flujo["connections"].items():
        if origen not in nombres:
            errores.append(f"la conexión sale de un nodo inexistente: {origen}")
        for grupo in salidas.get("main", []):
            for destino in grupo:
                if destino["node"] not in nombres:
                    errores.append(f"la conexión apunta a un nodo inexistente: {destino['node']}")

    if flujo["id"] != ID_FLUJO_ERRORES:
        if flujo.get("settings", {}).get("errorWorkflow") != ID_FLUJO_ERRORES:
            errores.append("no tiene asignado el flujo de errores")

    if not any(n["type"].endswith(DISPARADORES) for n in flujo["nodes"]):
        errores.append("no tiene ningún disparador")

    for nodo in flujo["nodes"]:
        for tipo, ref in nodo.get("credentials", {}).items():
            if ref.get("id") not in credenciales:
                errores.append(f"{nodo['name']}: credencial desconocida {tipo}/{ref.get('id')}")
            if "data" in ref:
                errores.append(f"{nodo['name']}: la credencial trae datos en claro")
        for hallazgo in claves_con_secretos(nodo.get("parameters", {})):
            errores.append(f"{nodo['name']}: posible secreto en {hallazgo}")

    return errores


def main() -> int:
    archivos = sorted((RAIZ / "workflows").glob("*.json"))
    if not archivos:
        print("No se encontraron workflows")
        return 1
    credenciales = credenciales_conocidas()
    hubo_errores = False
    for archivo in archivos:
        errores = revisar(archivo, credenciales)
        estado = "OK" if not errores else "ERROR"
        print(f"{estado:5} {archivo.name}")
        for error in errores:
            print(f"      - {error}")
        hubo_errores = hubo_errores or bool(errores)
    return 1 if hubo_errores else 0


if __name__ == "__main__":
    sys.exit(main())
