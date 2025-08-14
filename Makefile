.PHONY: sync test lint fmt docs serve gen-figures

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

gen-figures:
	uv run python scripts/make_figures.py

copy-figures:
	mkdir -p docs/assets/figures
	cp -f figures/*.png docs/assets/figures/
