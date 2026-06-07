PYTHON ?= python

.PHONY: install run-api run-ui test lint format

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
