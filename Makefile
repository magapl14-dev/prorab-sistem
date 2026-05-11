COMPOSE=docker compose -f infra/docker-compose.yml

.PHONY: up down logs migrate admin shell

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

migrate:
	$(COMPOSE) exec api alembic upgrade head

admin:
	$(COMPOSE) exec api python -m scripts.create_admin

shell:
	$(COMPOSE) exec api python

psql:
	$(COMPOSE) exec postgres psql -U welldom -d welldom

redis:
	$(COMPOSE) exec redis redis-cli

minio:
	@echo "MinIO console: http://localhost:9001 (minioadmin / minioadmin123)"

restart:
	$(COMPOSE) restart api

status:
	$(COMPOSE) ps
