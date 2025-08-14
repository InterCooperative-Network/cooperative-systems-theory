from __future__ import annotations

import cst as pkg

print("cst module:", pkg.__file__)
try:
    import cst.cli as cli
    print("cst.cli:", cli.__file__)
    app = getattr(cli, "app", None)
    print("has app:", app is not None)
    if app is not None:
        print("app type:", type(app))
        cmds = getattr(app, "commands", None)
        print("commands mapping:", cmds)
        if isinstance(cmds, dict):
            print("command keys:", sorted(cmds.keys()))
except Exception as e:
    print("import cst.cli failed:", e)
