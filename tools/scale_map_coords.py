# -*- coding: utf-8 -*-
"""
Scale all map coordinates (polygons, centers, place, pu_place) and map.width/height.
At fixed TripleA zoom 100%, effect is like zooming in (larger map in pixels).
units.scale is left unchanged.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# 1.15 = ~15 % näher, 1.20 = ~20 %, 1.25 = ~25 %  |  Rückgängig: SCALE = 1.0/1.2 und map.width/height manuell auf 10000/4286 setzen (siehe main).
SCALE = 1.20

PAIR_RE = re.compile(r"\((\d+)\s*,\s*(\d+)\)")


def scale_text(s: str) -> str:
    def repl(m: re.Match) -> str:
        x = int(round(int(m.group(1)) * SCALE))
        y = int(round(int(m.group(2)) * SCALE))
        return f"({x},{y})"

    return PAIR_RE.sub(repl, s)


def main() -> None:
    for name in ("polygons.txt", "centers.txt", "pu_place.txt", "place.txt"):
        p = ROOT / name
        raw = p.read_text(encoding="utf-8")
        p.write_text(scale_text(raw), encoding="utf-8", newline="\n")
        print(f"Scaled {name} with factor {SCALE}")

    mp = ROOT / "map.properties"
    text = mp.read_text(encoding="utf-8")

    def sub_dim(key: str, val: int) -> None:
        nonlocal text
        text, n = re.subn(
            rf"^{key}=\d+\s*$",
            f"{key}={val}",
            text,
            flags=re.MULTILINE,
        )
        if n != 1:
            raise SystemExit(f"Could not set {key} in map.properties exactly once")

    sub_dim("map.width", int(round(10000 * SCALE)))
    sub_dim("map.height", int(round(4286 * SCALE)))
    mp.write_text(text, encoding="utf-8", newline="\n")
    print(f"map.properties: map.width/map.height × {SCALE}")


if __name__ == "__main__":
    main()
