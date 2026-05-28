.PHONY: lint test typecheck validate format

lint:
	ruff check .

test:
	pytest

typecheck:
	mypy src tests

validate: lint typecheck test

format:
	ruff format .
