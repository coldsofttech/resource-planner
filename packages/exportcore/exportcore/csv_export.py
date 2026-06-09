from __future__ import annotations

import csv
import io


def export_to_csv(rows: list[dict[str, str]]) -> bytes:
    """Render rows to CSV bytes.

    Args:
        rows: Pre-formatted list of dicts where keys are display column names.

    Returns:
        UTF-8 encoded CSV bytes (BOM-free).
    """
    buffer = io.StringIO()
    if not rows:
        return buffer.getvalue().encode("utf-8")

    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")
