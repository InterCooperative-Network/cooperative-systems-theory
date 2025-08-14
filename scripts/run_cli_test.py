from __future__ import annotations

from cst.cli import app
from typer.testing import CliRunner

r = CliRunner().invoke(app, ["hello", "--name", "Matt"])
print("exit_code:", r.exit_code)
print("output:\n", r.output)
