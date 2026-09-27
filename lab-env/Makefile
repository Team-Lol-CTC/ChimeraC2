.PHONY: up down logs rebuild clean demo restart

up:
	docker compose up -d
	@echo "🟢 Lab running"

down:
	docker compose down

restart:
	docker compose restart

rebuild:
	docker compose up -d --build

logs:
	docker compose logs -f

clean:
	docker compose down -v --remove-orphans

demo: clean rebuild logs
