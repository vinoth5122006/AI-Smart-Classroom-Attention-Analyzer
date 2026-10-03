"""Rewrite Windows-style Git paths into real directories.

The GitHub Git Data API can store files as a single blob named
``modules\\attention_engine.py`` instead of ``modules/attention_engine.py``.
Linux Docker then has no ``modules`` package, so imports fail at boot.
"""

from __future__ import annotations

import sys
from pathlib import Path


def normalize(root: Path) -> int:
    moved = 0
    for path in list(root.rglob("*")):
        if not path.is_file() or "\\" not in path.name:
            continue
        dest = path.parent.joinpath(*path.name.split("\\"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        path.unlink(missing_ok=True)
        print(f"normalized {path.name} -> {dest.relative_to(root)}")
        moved += 1
    return moved


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    count = normalize(target)
    print(f"normalized {count} windows path(s) under {target}")
