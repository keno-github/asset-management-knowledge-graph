.PHONY: install dev test lint api ui ingest docker-up docker-down

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -v -m "not integration"

test-all:
	pytest -v

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

api:
	uvicorn amkg.api.app:app --reload --host 0.0.0.0 --port 8000

ui:
	cd frontend && npm run dev

ingest:
	python -m amkg.pipeline.orchestrator --steps all

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
