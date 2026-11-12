-- Datos de ejemplo. Todo es ficticio: empresas, personas, patentes y correos
-- (el dominio .test está reservado y no existe). Las fechas son relativas a
-- hoy para que la demo funcione cualquier día.

INSERT INTO ops.config (clave, valor, descripcion) VALUES
  ('aviso_dias',           '30', 'Días de anticipación para avisar vencimientos'),
  ('repetir_aviso_dias',   '7',  'Ventana antes de repetir un aviso al mismo cliente'),
  ('variacion_precio_pct', '8',  'Variación de precio (%) a partir de la cual se informa a compras'),
  ('preventivo_dias',      '45', 'Días sin servicio preventivo para abrir un ticket de contacto'),
  ('demo_espera_segundos', '',   'Si tiene valor, el recordatorio de turno espera ese tiempo en lugar de 24 h antes'),
  ('email_gerencia',       'gerencia@taller-ejemplo.test',     'Resumen semanal y escalamientos'),
  ('email_compras',        'compras@taller-ejemplo.test',      'Variaciones de precios de repuestos'),
  ('email_operaciones',    'operaciones@taller-ejemplo.test',  'Errores de los flujos'),
  ('email_taller',         'turnos@taller-ejemplo.test',       'Remitente de confirmaciones y recordatorios');

INSERT INTO ops.clientes (id, nombre, email_contacto, tipo_contrato, contrato_activo) VALUES
  (1, 'Alimentos Ejemplo S.A.',  'flota@alimentos-ejemplo.test',        'SUSCRIPCION', true),
  (2, 'Transporte Demo S.R.L.',  'mantenimiento@transporte-demo.test',  'PAY_PER_USE', true),
  (3, 'Distribuidora Modelo',    'logistica@distribuidora-modelo.test', 'SUSCRIPCION', true),
  (4, 'Servicios Ficticios S.A.', 'flota@servicios-ficticios.test',     'PAY_PER_USE', true),
  (5, 'Cooperativa Muestra',     'admin@cooperativa-muestra.test',      'SUSCRIPCION', false);

INSERT INTO ops.vehiculos (id, cliente_id, patente, marca_modelo, anio, km_actual, km_ultimo_service, intervalo_service_km) VALUES
  (1,  1, 'AA101BB', 'Furgón mediano',        2021,  58200,  50000, 10000),
  (2,  1, 'AA102BB', 'Furgón mediano',        2020,  71350,  61500, 10000),
  (3,  1, 'AA103BB', 'Pick-up doble cabina',  2022,  34100,  30000, 10000),
  (4,  2, 'AC201DD', 'Camión liviano',        2019, 142900, 133000, 10000),
  (5,  2, 'AC202DD', 'Camión liviano',        2018, 168000, 158200, 10000),
  (6,  2, 'AC203DD', 'Furgón chico',          2022,  41200,  36000, 10000),
  (7,  3, 'AD301EE', 'Utilitario',            2021,  62000,  55500, 10000),
  (8,  3, 'AD302EE', 'Utilitario',            2021,  59800,  52000, 10000),
  (9,  3, 'AD303EE', 'Pick-up simple',        2023,  18900,  10000, 10000),
  (10, 4, 'AE401FF', 'Furgón grande',         2020,  95500,  90200, 10000),
  (11, 4, 'AE402FF', 'Furgón grande',         2022,  47800,  42000, 10000),
  (12, 5, 'AF501GG', 'Utilitario',            2019, 120300, 110500, 10000),
  (13, 5, 'AF502GG', 'Utilitario',            2020,  99500,  90000, 10000),
  (14, 1, 'AA104BB', 'Furgón mediano',        2023,  12100,  10000, 10000);

INSERT INTO ops.mecanicos (id, nombre, nivel) VALUES
  (1, 'Rubén Ocampo',   'SENIOR'),
  (2, 'Silvia Benítez', 'SENIOR'),
  (3, 'Tomás Villalba', 'SEMI_SENIOR'),
  (4, 'Carla Duarte',   'JUNIOR');

INSERT INTO ops.vencimientos (vehiculo_id, tipo, fecha_vencimiento) VALUES
  (1,  'VTV',    current_date + 12),  (1,  'SEGURO', current_date + 200),
  (2,  'VTV',    current_date - 3),   (2,  'SEGURO', current_date + 25),
  (3,  'VTV',    current_date + 300), (3,  'SEGURO', current_date + 18),
  (4,  'VTV',    current_date + 8),   (4,  'SEGURO', current_date + 90),
  (5,  'VTV',    current_date + 28),  (5,  'SEGURO', current_date + 400),
  (6,  'VTV',    current_date + 120), (6,  'SEGURO', current_date + 5),
  (7,  'VTV',    current_date + 60),  (7,  'SEGURO', current_date + 75),
  (8,  'VTV',    current_date + 29),  (8,  'SEGURO', current_date + 210),
  (9,  'VTV',    current_date + 350), (9,  'SEGURO', current_date + 14),
  (10, 'VTV',    current_date - 10),  (10, 'SEGURO', current_date + 40),
  (11, 'VTV',    current_date + 22),  (11, 'SEGURO', current_date + 160),
  (12, 'VTV',    current_date + 10),  (12, 'SEGURO', current_date + 10),
  (14, 'VTV',    current_date + 500), (14, 'SEGURO', current_date + 19);

INSERT INTO ops.servicios (vehiculo_id, tipo, fecha) VALUES
  (1,  'PREVENTIVO', current_date - 20),
  (2,  'PREVENTIVO', current_date - 95),
  (6,  'PREVENTIVO', current_date - 63),
  (4,  'CORRECTIVO', current_date - 10),
  (5,  'CORRECTIVO', current_date - 33),
  (7,  'PREVENTIVO', current_date - 38),
  (8,  'PREVENTIVO', current_date - 120),
  (10, 'CORRECTIVO', current_date - 15),
  (11, 'CORRECTIVO', current_date - 70),
  (12, 'PREVENTIVO', current_date - 200);

-- Un turno ya reservado: sirve para probar que no se pisa un horario ocupado.
INSERT INTO ops.turnos (vehiculo_id, mecanico_id, motivo, fecha_hora, estado)
VALUES (1, 1, 'Service y revisión de frenos', (current_date + 3) + time '10:00', 'CONFIRMADO');

-- Catálogo inicial del proveedor (los mismos SKU y precios base que genera la API).
INSERT INTO ops.precios_repuestos (sku, descripcion, proveedor, precio, moneda) VALUES
  ('FIL-ACE-001', 'Filtro de aceite',                 'Repuestos Muestra S.A.',   9500.00, 'ARS'),
  ('FIL-AIR-002', 'Filtro de aire',                   'Repuestos Muestra S.A.',   8200.00, 'ARS'),
  ('FIL-COM-003', 'Filtro de combustible',            'Repuestos Muestra S.A.',  12400.00, 'ARS'),
  ('PAS-FRE-010', 'Pastillas de freno delanteras',    'Repuestos Muestra S.A.',  38500.00, 'ARS'),
  ('PAS-FRE-011', 'Pastillas de freno traseras',      'Repuestos Muestra S.A.',  29800.00, 'ARS'),
  ('DIS-FRE-012', 'Disco de freno',                   'Repuestos Muestra S.A.',  64200.00, 'ARS'),
  ('BAT-12V-020', 'Batería 12V 75Ah',                 'Repuestos Muestra S.A.', 185000.00, 'ARS'),
  ('BUJ-PRE-030', 'Bujía de precalentamiento',        'Repuestos Muestra S.A.',   7800.00, 'ARS'),
  ('COR-DIS-040', 'Correa de distribución',           'Repuestos Muestra S.A.',  52300.00, 'ARS'),
  ('AMO-DEL-050', 'Amortiguador delantero',           'Repuestos Muestra S.A.',  71500.00, 'ARS'),
  ('LIQ-REF-060', 'Líquido refrigerante 5 L',         'Repuestos Muestra S.A.',  13900.00, 'ARS'),
  ('ACE-MOT-070', 'Aceite de motor 15W40 5 L',        'Repuestos Muestra S.A.',  42500.00, 'ARS');

INSERT INTO ops.precios_historial (sku, precio, vigente_desde)
SELECT sku, precio, now() - interval '1 day' FROM ops.precios_repuestos;

-- Mantener las secuencias alineadas con los ids cargados a mano.
SELECT setval('ops.clientes_id_seq',  (SELECT max(id) FROM ops.clientes));
SELECT setval('ops.vehiculos_id_seq', (SELECT max(id) FROM ops.vehiculos));
SELECT setval('ops.mecanicos_id_seq', (SELECT max(id) FROM ops.mecanicos));
