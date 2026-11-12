.PHONY: up down demo test logs

up:
	docker compose up -d --build
	@echo "n8n:     http://localhost:5678"
	@echo "Mailpit: http://localhost:8025"

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

demo:
	sh scripts/demo.sh

test:
	docker run --rm -v "$(CURDIR)/api:/work" -w /work python:3.12-slim \
		sh -c "pip install -q --no-cache-dir -r requirements.txt && ruff check . && pytest -q"
