.PHONY: help up down setup reset build status logs psql clean

SHELL := /bin/bash
PY    := python

help:
	@echo "make up      - start the warehouse container"
	@echo "make setup   - up + install deps + reset to a clean seeded warehouse"
	@echo "make reset   - rebuild the warehouse clean, nothing broken"
	@echo "make build   - run dbt and record the run into meta.run_history"
	@echo "make status  - show which scenario is currently loaded"
	@echo "make psql    - open a shell against the warehouse"
	@echo "make down    - stop the container (keeps the volume)"
	@echo "make clean   - stop and delete the volume"

up:
	docker compose up -d
	@echo "waiting for postgres..."
	@until docker compose exec -T warehouse pg_isready -q; do sleep 1; done
	@echo "warehouse is up"

setup: up
	$(PY) -m pip install -r requirements.txt
	@test -f .env || cp .env.example .env
	$(PY) break.py --reset

reset:
	$(PY) break.py --reset

build:
	$(PY) tools/run_dbt.py

status:
	$(PY) break.py --status

logs:
	docker compose logs -f warehouse

psql:
	docker compose exec warehouse psql -U lineage -d warehouse

down:
	docker compose down

clean:
	docker compose down -v
	rm -rf .state dbt_project/target dbt_project/logs