# -*- coding: utf-8 -*-
"""Copy games/worldwar3.html into worldwar3.xml <property name="notes"> CDATA."""
from __future__ import annotations

from pathlib import Path

root = Path(__file__).resolve().parent.parent
html = (root / "games" / "worldwar3.html").read_text(encoding="utf-8")
if "]]>" in html:
    raise SystemExit("worldwar3.html must not contain ]]>")
xml = (root / "games" / "worldwar3.xml").read_text(encoding="utf-8")
s = xml.find('<property name="notes">')
if s == -1:
    raise SystemExit("no <property name=\"notes\"> in worldwar3.xml")
v = xml.find("<value><![CDATA[", s)
if v == -1:
    raise SystemExit("no CDATA start")
vi = v + len("<value><![CDATA[")
ve = xml.find("]]></value>", vi)
if ve == -1:
    raise SystemExit("no CDATA end")
new_xml = xml[:vi] + "\n" + html + "\n" + xml[ve:]
(root / "games" / "worldwar3.xml").write_text(new_xml, encoding="utf-8", newline="\n")
print("Embedded games/worldwar3.html into worldwar3.xml notes")
