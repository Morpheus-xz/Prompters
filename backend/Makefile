PYTHON := .venv/bin/python
ENV_FILE := $(if $(wildcard .env),--env-file .env,)
.PHONY: install dev test cov lint format typecheck deadcode audit clean
install:
	python3.11 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt
dev:
	$(PYTHON) -m uvicorn app.main:app --reload $(ENV_FILE)
test:
	$(PYTHON) -m pytest
cov: test
lint:
	$(PYTHON) -m ruff check app tests
	$(PYTHON) -m ruff format --check app tests
format:
	$(PYTHON) -m ruff check --fix app tests
	$(PYTHON) -m ruff format app tests
typecheck:
	$(PYTHON) -m mypy
deadcode:
	$(PYTHON) -m vulture
audit: lint typecheck deadcode cov
clean:
	$(PYTHON) -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('.pytest_cache', '.ruff_cache', '.mypy_cache', 'htmlcov')]"
