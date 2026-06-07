PYTHON ?= python
DOCKER_COMPOSE ?= docker compose

.PHONY: install run-api run-ui test lint format docker-build docker-up docker-down docker-logs

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run-api:
	$(PYTHON) -m uvicorn backend.app.main:app --reload

run-ui:
	$(PYTHON) -m streamlit run frontend/streamlit_app.py

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f
