from __future__ import annotations

from pathlib import Path


def project_root(start: str | None = None) -> Path:
    p = Path(start or __file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()

def load_theory_markdown() -> str:
    root = project_root(__file__)
    return (root / "docs" / "cst" / "theory.md").read_text(encoding="utf-8")
