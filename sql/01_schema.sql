-- Esquema operativo (ops) y de staging (stg) del taller.

CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS stg;

-- Parámetros que usan los flujos (umbrales, destinatarios, modo demo).
CREATE TABLE ops.config (
  clave       text PRIMARY KEY,
  valor       text NOT NULL DEFAULT '',
  descripcion text
);

CREATE FUNCTION ops.cfg_int(p_clave text) RETURNS int
  LANGUAGE sql STABLE AS
$$ SELECT valor::int FROM ops.config WHERE clave = p_clave $$;

CREATE TABLE ops.clientes (
  id              serial PRIMARY KEY,
  nombre          text NOT NULL,
  email_contacto  text NOT NULL,
  tipo_contrato   text NOT NULL CHECK (tipo_contrato IN ('SUSCRIPCION', 'PAY_PER_USE')),
  contrato_activo boolean NOT NULL DEFAULT true
);

CREATE TABLE ops.vehiculos (
  id                   serial PRIMARY KEY,
  cliente_id           int NOT NULL REFERENCES ops.clientes (id),
  patente              text NOT NULL UNIQUE,
  marca_modelo         text NOT NULL,
  anio                 int NOT NULL,
  km_actual            int NOT NULL DEFAULT 0,
  km_ultimo_service    int NOT NULL DEFAULT 0,
  intervalo_service_km int NOT NULL DEFAULT 10000,
  activo               boolean NOT NULL DEFAULT true
);

CREATE TABLE ops.mecanicos (
  id     serial PRIMARY KEY,
  nombre text NOT NULL,
  nivel  text NOT NULL CHECK (nivel IN ('JUNIOR', 'SEMI_SENIOR', 'SENIOR'))
);

CREATE TABLE ops.vencimientos (
  id                serial PRIMARY KEY,
  vehiculo_id       int NOT NULL REFERENCES ops.vehiculos (id),
  tipo              text NOT NULL CHECK (tipo IN ('VTV', 'SEGURO')),
  fecha_vencimiento date NOT NULL,
  UNIQUE (vehiculo_id, tipo)
);

CREATE TABLE ops.turnos (
  id                      serial PRIMARY KEY,
  vehiculo_id             int NOT NULL REFERENCES ops.vehiculos (id),
  mecanico_id             int REFERENCES ops.mecanicos (id),
  motivo                  text NOT NULL,
  fecha_hora              timestamptz NOT NULL,
  estado                  text NOT NULL DEFAULT 'PENDIENTE'
                          CHECK (estado IN ('PENDIENTE', 'CONFIRMADO', 'CANCELADO', 'REALIZADO')),
  creado_en               timestamptz NOT NULL DEFAULT now(),
  recordatorio_enviado_en timestamptz,
  UNIQUE (vehiculo_id, fecha_hora)
);

CREATE TABLE ops.servicios (
  id          serial PRIMARY KEY,
  vehiculo_id int NOT NULL REFERENCES ops.vehiculos (id),
  tipo        text NOT NULL CHECK (tipo IN ('PREVENTIVO', 'CORRECTIVO')),
  fecha       date NOT NULL
);

-- Cada aviso enviado deja una clave única: reejecutar un flujo no repite emails.
CREATE TABLE ops.notificaciones (
  id           serial PRIMARY KEY,
  clave        text NOT NULL UNIQUE,
  tipo         text NOT NULL,
  destinatario text NOT NULL,
  enviada_en   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.tickets_contacto (
  id         serial PRIMARY KEY,
  cliente_id int NOT NULL REFERENCES ops.clientes (id),
  motivo     text NOT NULL,
  estado     text NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO', 'CERRADO')),
  creado_en  timestamptz NOT NULL DEFAULT now()
);

-- Un solo ticket abierto por cliente y motivo.
CREATE UNIQUE INDEX ux_ticket_abierto
  ON ops.tickets_contacto (cliente_id, motivo) WHERE estado = 'ABIERTO';

CREATE TABLE ops.precios_repuestos (
  sku            text PRIMARY KEY,
  descripcion    text NOT NULL,
  proveedor      text NOT NULL,
  precio         numeric(12, 2) NOT NULL CHECK (precio > 0),
  moneda         text NOT NULL DEFAULT 'ARS',
  actualizado_en timestamptz NOT NULL DEFAULT now()
);

-- Solo se agrega una fila cuando el precio cambia.
CREATE TABLE ops.precios_historial (
  id            serial PRIMARY KEY,
  sku           text NOT NULL REFERENCES ops.precios_repuestos (sku),
  precio        numeric(12, 2) NOT NULL,
  vigente_desde timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ops.ejecuciones_error (
  id          serial PRIMARY KEY,
  workflow    text,
  nodo        text,
  mensaje     text,
  ocurrido_en timestamptz NOT NULL DEFAULT now()
);

-- Staging del ELT: primero se guarda lo crudo, después se transforma.
CREATE TABLE stg.precios_raw (
  id         bigserial PRIMARY KEY,
  lote_id    text NOT NULL,
  linea      int NOT NULL,
  contenido  jsonb NOT NULL,
  cargado_en timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE stg.etl_rechazos (
  id            bigserial PRIMARY KEY,
  lote_id       text NOT NULL,
  linea         int NOT NULL,
  motivo        text NOT NULL,
  contenido     text,
  registrado_en timestamptz NOT NULL DEFAULT now()
);
