-- Vistas que consultan los flujos de n8n.

-- Avisos de flota: vencimientos próximos y service por kilometraje.
-- Se omiten los vehículos que ya tienen un turno futuro.
CREATE VIEW ops.v_avisos AS
SELECT c.id AS cliente_id, c.nombre AS cliente, c.email_contacto,
       v.id AS vehiculo_id, v.patente, v.marca_modelo,
       x.tipo,
       (x.fecha_vencimiento - current_date) AS dias_restantes,
       format('%s vence el %s', x.tipo, to_char(x.fecha_vencimiento, 'DD/MM/YYYY')) AS detalle,
       (x.fecha_vencimiento < current_date) AS vencido
FROM ops.vencimientos x
JOIN ops.vehiculos v ON v.id = x.vehiculo_id AND v.activo
JOIN ops.clientes  c ON c.id = v.cliente_id AND c.contrato_activo
WHERE x.fecha_vencimiento <= current_date + ops.cfg_int('aviso_dias')
  AND NOT EXISTS (
    SELECT 1 FROM ops.turnos t
    WHERE t.vehiculo_id = v.id
      AND t.estado IN ('PENDIENTE', 'CONFIRMADO')
      AND t.fecha_hora > now())
UNION ALL
SELECT c.id, c.nombre, c.email_contacto,
       v.id, v.patente, v.marca_modelo,
       'SERVICE', NULL,
       format('Service por kilometraje: %s km desde el último (intervalo de %s km)',
              v.km_actual - v.km_ultimo_service, v.intervalo_service_km),
       false
FROM ops.vehiculos v
JOIN ops.clientes c ON c.id = v.cliente_id AND c.contrato_activo
WHERE v.activo
  AND (v.km_actual - v.km_ultimo_service) >= v.intervalo_service_km - 500
  AND NOT EXISTS (
    SELECT 1 FROM ops.turnos t
    WHERE t.vehiculo_id = v.id
      AND t.estado IN ('PENDIENTE', 'CONFIRMADO')
      AND t.fecha_hora > now());

-- Clientes con contrato activo sin servicio preventivo en los últimos N días.
CREATE VIEW ops.v_clientes_sin_preventivo AS
SELECT c.id AS cliente_id, c.nombre AS cliente, c.email_contacto, c.tipo_contrato,
       max(s.fecha) AS ultimo_preventivo,
       (current_date - max(s.fecha)) AS dias_sin_preventivo
FROM ops.clientes c
LEFT JOIN ops.vehiculos v ON v.cliente_id = c.id AND v.activo
LEFT JOIN ops.servicios s ON s.vehiculo_id = v.id AND s.tipo = 'PREVENTIVO'
WHERE c.contrato_activo
GROUP BY c.id
HAVING max(s.fecha) IS NULL
    OR current_date - max(s.fecha) > ops.cfg_int('preventivo_dias');

-- Último precio contra el anterior de cada repuesto.
CREATE VIEW ops.v_variacion_precios AS
SELECT sku, descripcion, anterior, actual,
       round((actual - anterior) / anterior * 100, 1) AS variacion_pct
FROM (
  SELECT h.sku, p.descripcion, h.precio AS actual,
         lag(h.precio) OVER (PARTITION BY h.sku ORDER BY h.vigente_desde, h.id) AS anterior,
         row_number()  OVER (PARTITION BY h.sku ORDER BY h.vigente_desde DESC, h.id DESC) AS rn
  FROM ops.precios_historial h
  JOIN ops.precios_repuestos p USING (sku)
) t
WHERE rn = 1 AND anterior IS NOT NULL AND anterior > 0;
