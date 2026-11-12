-- n8n guarda sus propias tablas en una base aparte.
CREATE DATABASE n8n;

-- Las fechas del taller se interpretan en hora argentina.
ALTER DATABASE flota SET timezone TO 'America/Argentina/Buenos_Aires';
