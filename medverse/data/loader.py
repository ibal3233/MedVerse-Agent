from __future__ import annotations
from pathlib import Path
import csv, json, hashlib
from typing import Any

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def load_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    encodings = ["utf-8-sig", "utf-8", "cp949"]
    last_error = None
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return reader.fieldnames or [], rows
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error
