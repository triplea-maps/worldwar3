# -*- coding: utf-8 -*-
"""
Territory production (PUs) from nominal GDP ~2024/2025 (USD bn), log-scaled.
Land: 1–9, sea: 0. Then light coalition balancing (Allies vs Axis ~±2%).
Run: python rebalance_pu.py (from tools/)
"""
from __future__ import annotations

import math
import re
from pathlib import Path

XML_PATH = Path(__file__).resolve().parent.parent / "games" / "worldwar3.xml"

ALLIES = frozenset({"Europe", "USA", "GlobalAllies"})
AXIS = frozenset({"Russians", "China", "GlobalAxis"})


def pu_from_gdp(gdp_bn: float) -> int:
    """GDP → PU 1..9 (compressed so rich countries do not exceed 9)."""
    if gdp_bn < 2.5:
        return 1
    v = 3.45 * math.log10(gdp_bn) - 5.05
    return max(1, min(9, int(round(v))))


def parse_water_territories(xml: str) -> set[str]:
    return {
        m.group(1)
        for m in re.finditer(r'<territory name="([^"]+)"\s+water="true"', xml)
    }


def parse_territory_owners(xml: str) -> dict[str, str]:
    """From ownerInitialize: territory → player."""
    return {
        m.group(1): m.group(2)
        for m in re.finditer(
            r'<territoryOwner territory="([^"]+)" owner="([^"]+)"/>',
            xml,
        )
    }


def balance_coalition_income(
    pu: dict[str, int],
    owner: dict[str, str],
    water: set[str],
    *,
    target: float = 1.025,
    lo: float = 1.01,
    hi: float = 1.04,
    max_iter: int = 80,
) -> dict[str, int]:
    """
    Passt nur Allies- und Axis-Territorien an (Neutral unverändert).
    Ziel: Summe(Allies) / Summe(Axis) ≈ target (leichter realistischer West-/Verbündeten-Vorteil),
    Toleranz [lo, hi] nach Rundung.
    """
    new = dict(pu)

    def totals() -> tuple[float, float]:
        a = sum(
            new[t]
            for t in new
            if t not in water and owner.get(t) in ALLIES
        )
        x = sum(
            new[t]
            for t in new
            if t not in water and owner.get(t) in AXIS
        )
        return float(a), float(x)

    for _ in range(max_iter):
        a, x = totals()
        if x < 1.0:
            break
        r = a / x
        if lo <= r <= hi:
            break
        fa = math.sqrt(target / r)
        fx = math.sqrt(r / target)
        for t in list(new):
            if t in water or new[t] < 1:
                continue
            o = owner.get(t)
            if o in ALLIES:
                new[t] = max(1, min(9, int(round(new[t] * fa))))
            elif o in AXIS:
                new[t] = max(1, min(9, int(round(new[t] * fx))))

    # Integer caps (many at 9) often block convergence → nudge ±1 per iteration
    for _ in range(500):
        a, x = totals()
        if x < 1.0:
            break
        r = a / x
        if lo <= r <= hi:
            break
        if r > hi:
            cand = [
                t
                for t in new
                if t not in water and owner.get(t) in ALLIES and new[t] > 1
            ]
            if not cand:
                cand = [
                    t
                    for t in new
                    if t not in water and owner.get(t) in AXIS and new[t] < 9
                ]
                if cand:
                    t = min(cand, key=lambda z: new[z])
                    new[t] += 1
                else:
                    break
            else:
                t = max(cand, key=lambda z: new[z])
                new[t] -= 1
        else:
            cand = [
                t
                for t in new
                if t not in water and owner.get(t) in AXIS and new[t] > 1
            ]
            if not cand:
                cand = [
                    t
                    for t in new
                    if t not in water and owner.get(t) in ALLIES and new[t] < 9
                ]
                if cand:
                    t = min(cand, key=lambda z: new[z])
                    new[t] += 1
                else:
                    break
            else:
                t = max(cand, key=lambda z: new[z])
                new[t] -= 1
    return new


def build_gdp() -> dict[str, float]:
    g: dict[str, float] = {}

    # USA ~30,000 bn USD, state shares
    us_w = {
        "California": 0.147,
        "Texas": 0.096,
        "NY": 0.086,
        "New York": 0.056,
        "Florida": 0.066,
        "Carolina": 0.046,
        "Washington": 0.036,
        "Tennesse": 0.029,
        "Minnesota": 0.023,
        "LA": 0.023,
        "Nevada": 0.019,
        "Nebraska": 0.013,
        "Dakota": 0.011,
        "Montana": 0.009,
        "Alaska": 0.008,
        "Hawaii": 0.004,
    }
    s_us = sum(us_w.values())
    for k, w in us_w.items():
        g[k] = 30_000.0 * (w / s_us)

    g.update(
        {
            "Ontario": 900,
            "Quebec": 520,
            "Alberta": 400,
            "British Columbia": 330,
            "Manitoba": 85,
            "Northwest Canada": 45,
            "Yukon": 6,
            "Nunavut": 4,
            "W. Mexico": 980,
            "E. Mexico": 870,
        }
    )

    # China ~18,800 bn (map regions), North Korea separate
    cn_raw = [
        ("Beijing", 690),
        ("Shanghai", 720),
        ("Hong Kong", 410),
        ("Kwangtung", 1950),
        ("Nanjing", 2100),
        ("Jinan", 820),
        ("Qingdao", 820),
        ("Wuhan", 1250),
        ("Chongqing", 520),
        ("Xi'An", 520),
        ("Kunming", 380),
        ("Guangxi", 420),
        ("Changde", 780),
        ("Harbin", 720),
        ("Hulunbuir", 320),
        ("Chifeng", 380),
        ("Tibet", 85),
        ("Xinjiang", 320),
        ("Qinghai", 55),
        ("Yinchuan", 180),
    ]
    sc = 18_800.0 / sum(w for _, w in cn_raw)
    for k, w in cn_raw:
        g[k] = w * sc
    g["North Korea"] = 32

    # Russia ~2,050 bn (RF regions on this map only)
    ru_raw = [
        ("Moscow", 520),
        ("St Petersburg", 210),
        ("Kaliningrad", 28),
        ("Crimea", 18),
        ("Volgograd", 85),
        ("Novgorod", 55),
        ("Smolensk", 45),
        ("Murmansk", 42),
        ("Arkhangelsk", 38),
        ("Vologda", 48),
        ("Vladivostok", 95),
        ("Khabarovsk", 72),
        ("Amurskaya", 38),
        ("Buryatia", 28),
        ("Irkutsk", 62),
        ("Yakutsk", 35),
        ("Magadan", 18),
        ("Kamchatka", 12),
        ("Okhotsk", 15),
        ("Pevek", 8),
        ("Siberia", 55),
        ("NW. Siberia", 120),
        ("Novo-Sibirsk", 95),
        ("Omsk", 72),
        ("Sverdlovsk", 110),
        ("Ulyanovsk", 48),
        ("W. Siberia", 85),
        ("E. Siberia", 42),
        ("S. Siberia", 38),
    ]
    sr = 2_050.0 / sum(w for _, w in ru_raw)
    for k, w in ru_raw:
        g[k] = w * sr

    g.update(
        {
            "Belarus": 72,
            "Caucasus": 185,
            "Ukraine": 195,
            "UK": 3_550,
            "France": 3_150,
            "Germany": 4_650,
            "Italy": 2_350,
            "Spain": 1_700,
            "Poland": 865,
            "Benelux": 1_820,
            "Austro-Slovenia": 610,
            "Balkan": 245,
            "Baltic States": 135,
            "Sweden": 610,
            "Finland": 305,
            "Norway": 515,
            "Greece": 255,
            "Portugal": 295,
            "Romania": 355,
            "Bulgaria": 105,
            "Hungary": 225,
            "Ireland": 575,
            "Iceland": 32,
            "Moldova": 17,
            "Georgia": 33,
            "W. Turkey": 920,
            "E. Turkey": 360,
            "Switzerland": 935,
            "Greenland": 3.5,
            "French Guiana": 5.5,
        }
    )

    in_raw = [
        ("New Delhi", 320),
        ("Uttar Pradesh", 310),
        ("Bihar", 88),
        ("Gujarat", 275),
        ("Karnataka", 360),
        ("Tamil Nadu", 400),
        ("Madhya Pradesh", 155),
        ("Orissa", 105),
        ("Jammu Kashmir", 38),
    ]
    si = 4_100.0 / sum(w for _, w in in_raw)
    for k, w in in_raw:
        g[k] = w * si

    g.update(
        {
            "Bangladesh": 465,
            "Pakistan": 385,
            "Nepal": 45,
            "Bhutan": 3.5,
            "Sri Lanka": 88,
            "Japan": 1_850,
            "Tokio": 2_250,
            "South Korea": 1_780,
            "Taiwan": 790,
            "Mongolia": 22,
            "Thailand": 530,
            "Vietnam": 470,
            "Myanmar": 78,
            "Laos": 20,
            "Cambodia": 34,
            "Philippines": 470,
            "Indonesia": 920,
            "Jakarta": 530,
            "Papua New Guinea": 32,
            "W. Australia": 520,
            "M. Australia": 180,
            "Queensland": 480,
            "Victoria": 540,
            "New Zealand": 255,
            "Israel": 530,
            "Jordan": 55,
            "Syria": 22,
            "Iraq": 280,
            "Iran": 410,
            "Saudi Arabia": 1_180,
            "United Arab Emirates": 565,
            "Oman": 115,
            "Yemen": 22,
            "Egypt": 295,
            "Cairo": 185,
            "Morocco": 155,
            "Algeria": 270,
            "Libya": 48,
            "Tunisia": 54,
            "South Africa": 380,
            "Cape Town": 95,
            "Nigeria": 510,
            "Kenya": 118,
            "Ethiopia": 205,
            "Ghana": 84,
            "Senegal": 31,
            "Liberia": 4.2,
            "Botswana": 22,
            "Namibia": 13,
            "Angola": 95,
            "DRC": 75,
            "Congo": 15,
            "Gabon": 22,
            "Cameroon": 53,
            "CAR": 3,
            "Chad": 18,
            "Niger": 17,
            "Mali": 22,
            "Burkina Faso": 22,
            "Guinea": 24,
            "Suda": 48,
            "Uganda": 55,
            "Zambia": 29,
            "Zimbabwe": 32,
            "Mozambique": 22,
            "Madagascar": 16,
            "Tanzania": 84,
            "Somalia": 12,
            "South Sudan": 6,
            "Mauritania": 11,
            "Cote dIvoire": 86,
            "Argentina": 640,
            "Chile": 360,
            "Peru": 285,
            "Columbia": 465,
            "Venezuela": 130,
            "Ecuador": 122,
            "Bolivia": 48,
            "Paraguay": 45,
            "Uruguay": 77,
            "Guatemala": 102,
            "Panama": 90,
            "Cuba": 125,
            "Dominican Republic": 127,
            "Guyana": 20,
            "N. Brazil": 680,
            "S. Brazil": 920,
            "Rio de Janeiro": 320,
            "Kazakhstan": 285,
            "Uzbekistan": 115,
            "Tajikistan": 12,
            "Turkmenistan": 82,
            "Afghanistan": 18,
        }
    )

    return g


BLOCK_RE = re.compile(
    r'<attachment\s+name="territoryAttachment"[^>]*attachTo="([^"]+)"[^>]*type="territory"[^>]*>.*?</attachment>',
    re.DOTALL,
)
PROD_RE = re.compile(r'(<option name="production" value=")(\d+)(")')


def main() -> None:
    xml = XML_PATH.read_text(encoding="utf-8")
    water = parse_water_territories(xml)
    owners = parse_territory_owners(xml)
    gdp = build_gdp()

    pu_map: dict[str, int] = {}
    for m in BLOCK_RE.finditer(xml):
        name = m.group(1)
        if name in water:
            pu_map[name] = 0
        else:
            pu_map[name] = pu_from_gdp(float(gdp.get(name, 42.0)))

    pu_map = balance_coalition_income(pu_map, owners, water)

    def repl_block(m: re.Match) -> str:
        block = m.group(0)
        name = m.group(1)
        pu = pu_map[name]
        nb, nsub = PROD_RE.subn(r"\g<1>%d\g<3>" % pu, block, count=1)
        if nsub != 1:
            raise RuntimeError(f"No production option in block: {name[:40]}")
        return nb

    new_xml, n = BLOCK_RE.subn(repl_block, xml)
    if n == 0:
        raise SystemExit("No territoryAttachment blocks found.")

    XML_PATH.write_text(new_xml, encoding="utf-8", newline="\n")
    print(f"Updated {n} territoryAttachment blocks in {XML_PATH}")

    a = sum(
        pu_map[t] for t in pu_map if t not in water and owners.get(t) in ALLIES
    )
    x = sum(
        pu_map[t] for t in pu_map if t not in water and owners.get(t) in AXIS
    )
    print(f"Coalition PU sum (starting ownership): Allies {a}, Axis {x}, ratio {a/x:.3f}")

    top = []
    for name, p in pu_map.items():
        if name not in water:
            top.append((p, name, gdp.get(name)))
    top.sort(reverse=True)
    print("Top 15 PU (land):")
    for pu, name, gv in top[:15]:
        print(f"  {pu:2d}  {name:22s}  GDP~{gv}")
    land_sum = sum(p for p, nm, _ in top)
    print("Total land PU (including Neutral):", land_sum)


if __name__ == "__main__":
    main()
