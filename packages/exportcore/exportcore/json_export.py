from __future__ import annotations

import json


def export_to_json(rows: list[dict[str, str]]) -> bytes:
    """Render rows to JSON bytes.

    Args:
        rows: Pre-formatted list of dicts where keys are display column names.

    Returns:
        UTF-8 encoded JSON bytes representing a JSON array.
    """
    return json.dumps(rows, ensure_ascii=False, indent=2).encode("utf-8")
