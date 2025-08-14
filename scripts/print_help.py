from __future__ import annotations

import click
from cst.cli import app

with click.Context(app) as ctx:
    print(app.get_help(ctx))
print('commands:', list(getattr(app, 'commands', {}).keys()))
