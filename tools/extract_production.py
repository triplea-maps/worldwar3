# -*- coding: utf-8 -*-
import re
from pathlib import Path

text = Path(__file__).resolve().parent.parent / "games" / "worldwar3.xml"
text = text.read_text(encoding="utf-8")
items = []
for m in re.finditer(
    r'attachTo="([^"]+)" javaClass="games\.strategy\.triplea\.attachments\.TerritoryAttachment"',
    text,
):
    start = m.end()
    sub = text[start : start + 500]
    pm = re.search(r'<option name="production" value="(\d+)"', sub)
    if pm:
        items.append((m.group(1), int(pm.group(1))))
print("count", len(items))
for t, p in sorted(items, key=lambda x: -x[1])[:30]:
    print(p, t)
print("sum", sum(p for _, p in items))
