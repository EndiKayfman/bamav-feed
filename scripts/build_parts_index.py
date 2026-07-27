#!/usr/bin/env python3
"""Build parts.json from bamper.csv and avby.csv for the QR landing page."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def merge(parts: dict[str, dict[str, str]], key: str, entry: dict[str, str]) -> None:
    key = key.strip().upper()
    if not key:
        return
    prev = parts.get(key)
    if not prev:
        parts[key] = entry
        return
    parts[key] = {
        "w": entry["w"] or prev["w"],
        "p": entry["p"] or prev["p"],
    }


def first_photo(raw: str) -> str:
    for part in raw.split(","):
        url = part.strip()
        if url.startswith("http://") or url.startswith("https://"):
            return url
    return ""


def load_csv(path: Path) -> list[list[str]]:
    text = path.read_text(encoding="utf-8")
    return list(csv.reader(text.splitlines(), delimiter=";"))


def main() -> None:
    parts: dict[str, dict[str, str]] = {}

    bamper_rows = load_csv(ROOT / "bamper.csv")
    if len(bamper_rows) >= 2:
        header = bamper_rows[0]
        id_idx = header.index("ID_EXT")
        oem_idx = header.index("ОРИГИНАЛЬНЫЙ НОМЕР")
        wh_idx = header.index("СКЛАДСКАЯ ИНФОРМАЦИЯ")
        photo_idx = header.index("ФОТО")
        for row in bamper_rows[1:]:
            entry = {
                "w": row[wh_idx] if wh_idx < len(row) else "",
                "p": first_photo(row[photo_idx] if photo_idx < len(row) else ""),
            }
            if id_idx < len(row):
                merge(parts, row[id_idx], entry)
            if oem_idx < len(row):
                merge(parts, row[oem_idx], entry)

    avby_rows = load_csv(ROOT / "avby.csv")
    if len(avby_rows) >= 2:
        header = avby_rows[0]
        id_idx = header.index("ID")
        oem_idx = header.index("OEM")
        photo_idx = header.index("PHOTO")
        for row in avby_rows[1:]:
            entry = {
                "w": "",
                "p": first_photo(row[photo_idx] if photo_idx < len(row) else ""),
            }
            if id_idx < len(row):
                merge(parts, row[id_idx], entry)
            if oem_idx < len(row):
                merge(parts, row[oem_idx], entry)

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "parts": parts,
    }
    out = ROOT / "parts.json"
    out.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {out} ({len(parts)} parts)")


if __name__ == "__main__":
    main()
