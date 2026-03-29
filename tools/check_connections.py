# -*- coding: utf-8 -*-
"""Prüft worldwar3.xml: Territorien, Verbindungen, Duplikate, unbekannte Namen."""
from __future__ import annotations

import re
from pathlib import Path

XML = Path(__file__).resolve().parent.parent / "games" / "worldwar3.xml"


def norm_pairs(pairs: set[tuple[str, str]]) -> set[tuple[str, str]]:
    return {tuple(sorted((a, b))) for a, b in pairs}


def main() -> None:
    text = XML.read_text(encoding="utf-8")
    terrs = set(re.findall(r'<territory name="([^"]+)"', text))
    conns = re.findall(r'<connection t1="([^"]+)" t2="([^"]+)"', text)

    pairs: set[tuple[str, str]] = set()
    dups: list[tuple[str, str]] = []
    bad: list[tuple[str, str]] = []
    self_loops: list[tuple[str, str]] = []

    for a, b in conns:
        if a not in terrs or b not in terrs:
            bad.append((a, b))
            continue
        if a == b:
            self_loops.append((a, b))
            continue
        key = tuple(sorted((a, b)))
        if key in pairs:
            dups.append((a, b))
        pairs.add(key)

    print("Territories:", len(terrs))
    print("Connection entries:", len(conns))
    print("Unique pairs:", len(pairs))

    if bad:
        print("\n*** UNKNOWN TERRITORY NAMES (typos?) ***")
        for a, b in bad[:40]:
            na = "(??)" if a not in terrs else ""
            nb = "(??)" if b not in terrs else ""
            print(f"  {a}{na} <-> {b}{nb}")
        if len(bad) > 40:
            print(f"  ... +{len(bad) - 40} more")

    if self_loops:
        print("\n*** SELF-CONNECTIONS ***")
        for x in self_loops:
            print(x)

    if dups:
        print("\n*** DUPLICATE PAIRS ***")
        for x in dups[:30]:
            print(x)

    connected: set[str] = set()
    for a, b in conns:
        if a in terrs and b in terrs:
            connected.add(a)
            connected.add(b)

    isolated = sorted(terrs - connected)
    if isolated:
        print("\n*** OHNE VERBINDUNG (isoliert) ***")
        for t in isolated:
            print(f"  {t}")

    land_only = {t for t in terrs if "Sea" not in t and not re.match(r"^S\d+$", t)}
    low: list[tuple[str, int]] = []
    for t in sorted(land_only):
        n = sum(
            1
            for a, b in conns
            if (a == t or b == t) and a in terrs and b in terrs
        )
        if n <= 1:
            low.append((t, n))

    if low:
        print("\n*** LAND WITH AT MOST 1 CONNECTION (unusual) ***")
        for t, n in low[:40]:
            print(f"  {t}: {n}")
        if len(low) > 40:
            print(f"  ... +{len(low) - 40} more")

    conn_path = Path(__file__).resolve().parent.parent / "connections.txt"
    if conn_path.exists():
        ct = conn_path.read_text(encoding="utf-8")
        cc = set(re.findall(r'<connection t1="([^"]+)" t2="([^"]+)"', ct))
        xn = norm_pairs(set(conns))
        cn = norm_pairs(cc)
        print("\n--- Compare with connections.txt ---")
        print("XML:", len(xn), "connections.txt:", len(cn))
        only_xml = xn - cn
        only_ct = cn - xn
        if only_xml:
            print("Only in XML:", len(only_xml))
            for p in sorted(only_xml)[:25]:
                print(" ", p)
        if only_ct:
            print("Only in connections.txt:", len(only_ct))
            for p in sorted(only_ct)[:25]:
                print(" ", p)
        if not only_xml and not only_ct:
            print("Same connection set (unordered pairs).")

    print("\nDone.")


if __name__ == "__main__":
    main()
