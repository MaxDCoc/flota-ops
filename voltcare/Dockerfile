# VoltCare Analytics (repo propio) construido desde GitHub.
# Se clona dentro de la imagen para que el build no dependa del sistema operativo
# ni de contextos git de Docker Compose.
FROM golang:1.26

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*

# Rama o tag del repo a usar.
ARG VOLTCARE_REF=main
RUN git clone --depth 1 --branch "${VOLTCARE_REF}" \
      https://github.com/MaxDCoc/VoltCare-Analytics.git /app

WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# La API Go espera estar en voltcare-api/ (lee ahí su archivo .env)
# y llama a los scripts de Python por la ruta absoluta /app/notebooks.
WORKDIR /app/voltcare-api
RUN go mod download && go build -o /usr/local/bin/voltcare cmd/main.go

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=12 \
  CMD curl -fs http://localhost:8080/health || exit 1

CMD ["voltcare"]
