.PHONY: sync test lint fmt docs serve

sync:
	uv sync --all-extras --dev

test:
	uv run pytest -q

lint:
	ruff check .

fmt:
	ruff check --fix .

docs:
	uv run mkdocs build

serve:
	uv run mkdocs serve -a 127.0.0.1:8000
