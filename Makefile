.PHONY: check-venv lint test typecheck validate format

PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff

check-venv:
	@test -d .venv || (echo "Missing .venv. Create it with: python3.11 -m venv .venv && source .venv/bin/activate && python -m pip install -e '.[dev]'" && exit 1)

lint: check-venv
	$(RUFF) check .

test: check-venv
	$(PYTHON) -m pytest

typecheck: check-venv
	$(PYTHON) -m mypy src tests

validate: check-venv lint typecheck test

format: check-venv
	$(RUFF) format .
