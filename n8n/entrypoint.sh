#!/bin/sh
# Importa credenciales y workflows y recién después arranca n8n.
# Reimportar en cada arranque es seguro: los ids son fijos y se actualizan.
set -eu

CREDENCIALES=/tmp/credentials.json

sed \
  -e "s|__POSTGRES_USER__|${POSTGRES_USER}|g" \
  -e "s|__POSTGRES_PASSWORD__|${POSTGRES_PASSWORD}|g" \
  /opt/flota/n8n/credentials.template.json > "$CREDENCIALES"

n8n import:credentials --input="$CREDENCIALES"
rm -f "$CREDENCIALES"

n8n import:workflow --separate --input=/opt/flota/workflows
n8n update:workflow --all --active=true

exec n8n start
