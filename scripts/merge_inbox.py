#!/usr/bin/env python3
"""Merge inbox/avby-*.csv into avby.csv (upsert by ID), then clean inbox."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"
AVBY = ROOT / "avby.csv"


def load_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    text = path.read_text(encoding="utf-8")
    rows = list(csv.reader(text.splitlines(), delimiter=";"))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def write_rows(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main() -> int:
    if not INBOX.exists():
        print("No inbox/ directory")
        return 0

    inbox_files = sorted(INBOX.glob("avby-*.csv"))
    if not inbox_files:
        print("No inbox avby files")
        return 0

    if AVBY.exists():
        header, rows = load_rows(AVBY)
    else:
        header, rows = [], []

    if not header:
        header, _ = load_rows(inbox_files[0])
        rows = []

    try:
        id_idx = header.index("ID")
    except ValueError:
        print("avby.csv has no ID column", file=sys.stderr)
        return 1

    id_to_index: dict[str, int] = {}
    for i, row in enumerate(rows):
        while len(row) < len(header):
            row.append("")
        key = row[id_idx].strip().upper()
        if key:
            id_to_index[key] = i

    added = 0
    updated = 0
    for path in inbox_files:
        _, incoming = load_rows(path)
        for row in incoming:
            while len(row) < len(header):
                row.append("")
            if len(row) > len(header):
                row = row[: len(header)]
            key = row[id_idx].strip().upper() if id_idx < len(row) else ""
            if not key:
                continue
            existing = id_to_index.get(key)
            if existing is None:
                id_to_index[key] = len(rows)
                rows.append(row)
                added += 1
            else:
                rows[existing] = row
                updated += 1

    write_rows(AVBY, header, rows)

    for path in inbox_files:
        path.unlink(missing_ok=True)

    # Remove empty inbox dir marker files if any
    for leftover in INBOX.glob("*"):
        if leftover.is_file() and leftover.name.startswith("."):
            continue

    print(f"Merged inbox → avby.csv: +{added} new, ~{updated} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
