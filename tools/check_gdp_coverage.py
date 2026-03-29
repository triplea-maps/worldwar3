import re
from pathlib import Path

import rebalance_pu as r

xml = Path(__file__).resolve().parent.parent / "games" / "worldwar3.xml"
text = xml.read_text(encoding="utf-8")
water = r.parse_water_territories(text)
names = set(re.findall(r'<attachment\s+name="territoryAttachment"[^>]*attachTo="([^"]+)"', text))
gdp = r.build_gdp()
missing = sorted(n for n in names if n not in water and n not in gdp)
print("Land territories without explicit GDP:", len(missing))
for n in missing:
    print(" ", n)
