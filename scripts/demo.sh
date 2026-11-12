#!/bin/sh
# Dispara los flujos para verlos funcionar. Requiere `docker compose up -d` corriendo.
# Después mirá los emails en http://localhost:8025 y los datos con psql (ver al final).
set -eu

N8N=http://localhost:5678
EJECUTAR="docker compose exec -T n8n n8n execute --id"

paso() { printf '\n== %s\n' "$1"; }

paso "1. Sincronizar odómetros"
$EJECUTAR=flota-00-odometros > /dev/null && echo "listo"

paso "2. Avisos de vencimientos (un email por cliente)"
$EJECUTAR=flota-01-vencimientos > /dev/null && echo "listo"

paso "3. Lista de precios del proveedor (ETL)"
$EJECUTAR=flota-03-precios > /dev/null && echo "listo"

paso "4. Seguimiento preventivo (VoltCare + tickets de contacto)"
$EJECUTAR=flota-04-preventivo > /dev/null && echo "listo"

paso "5. Pedido de turno por webhook"
set -- $(docker compose exec -T api python -c "
from datetime import date, timedelta
from app.flota import disponibilidad
d = date.today() + timedelta(days=3)
while not disponibilidad(d):
    d += timedelta(days=1)
print(d, disponibilidad(d)[0])
")
FECHA=$1
HORA=$2
curl -s -X POST "$N8N/webhook/turno" \
  -H 'Content-Type: application/json' \
  -d "{\"patente\":\"AA103BB\",\"fecha\":\"$FECHA\",\"hora\":\"$HORA\",\"motivo\":\"Revisión de frenos\"}"
echo

cat <<'FIN'

Listo. Dónde mirar:
  Emails .......... http://localhost:8025
  Flujos ......... http://localhost:5678
  Rechazos del ETL: docker compose exec postgres psql -U flota -d flota -c "SELECT linea, motivo FROM stg.etl_rechazos ORDER BY id DESC LIMIT 10"
  Tickets ......... docker compose exec postgres psql -U flota -d flota -c "SELECT * FROM ops.tickets_contacto"
FIN
