# -*- coding: utf-8 -*-
"""Writes the connection block in connections.txt from worldwar3.xml (sorted)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
xml = (ROOT / "games" / "worldwar3.xml").read_text(encoding="utf-8")
conn_txt = ROOT / "connections.txt"
conns = re.findall(r'<connection t1="([^"]+)" t2="([^"]+)"', xml)
lines = [f'<connection t1="{a}" t2="{b}"/>' for a, b in sorted(conns)]
marker = "<!-- Territory Connections -->"
full = conn_txt.read_text(encoding="utf-8")
if marker not in full:
    raise SystemExit(f"{marker} not found in connections.txt")
head, _, _ = full.partition(marker)
new = head.rstrip() + "\n\n" + marker + "\n" + "\n".join(lines) + "\n"
conn_txt.write_text(new, encoding="utf-8", newline="\n")
print(f"{len(lines)} connections written to connections.txt.")
