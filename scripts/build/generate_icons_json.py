"""
Generate apps/web/static/js/data/bootstrap-icons.json
from the Bootstrap Icons font CSS (fetched from CDN).

Usage:
    python scripts/build/generate_icons_json.py

Output format:
{
  "all": ["0-circle", "0-circle-fill", ...],          # flat sorted list of all names
  "categories": [{"id": "arrows", "label": "Arrows"}, ...],
  "icons": { "arrows": ["arrow-down", ...], ... }
}

Re-run whenever you upgrade bootstrap-icons to pick up new icons.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BI_VERSION = "1.11.3"
CDN_URL = f"https://cdn.jsdelivr.net/npm/bootstrap-icons@{BI_VERSION}/font/bootstrap-icons.min.css"
OUTPUT = Path(__file__).parents[2] / "apps/web/static/js/data/bootstrap-icons.json"

# Category keyword rules: (category_id, label, [substrings that place icon here])
# Checked in order; first match wins. Icons not matched fall into "other".
CATEGORY_RULES = [
    (
        "arrows",
        "Arrows",
        [
            "arrow",
            "chevron",
            "caret",
            "skip-",
            "box-arrow",
            "cursor",
            "shift",
            "escape",
            "backspace",
        ],
    ),
    (
        "media",
        "Media",
        [
            "play",
            "pause",
            "stop",
            "record",
            "skip",
            "rewind",
            "fast-forward",
            "volume",
            "music",
            "camera",
            "film",
            "youtube",
            "spotify",
            "soundwave",
            "mic",
            "headphone",
            "speaker",
            "broadcast",
            "camera-video",
            "badge",
            "eject",
            "shuffle",
            "repeat",
            "disc",
        ],
    ),
    (
        "communication",
        "Communication",
        [
            "chat",
            "envelope",
            "telephone",
            "phone",
            "inbox",
            "reply",
            "send",
            "rss",
            "bell",
            "megaphone",
            "broadcast",
            "wifi",
            "reception",
            "signal",
            "at",
            "voicemail",
            "mailbox",
        ],
    ),
    (
        "data",
        "Data",
        [
            "bar-chart",
            "pie-chart",
            "graph",
            "diagram",
            "table",
            "database",
            "server",
            "hdd",
            "cpu",
            "memory",
            "terminal",
            "spreadsheet",
            "file-spreadsheet",
            "clipboard-data",
        ],
    ),
    (
        "device",
        "Device",
        [
            "laptop",
            "phone",
            "tablet",
            "watch",
            "tv",
            "display",
            "keyboard",
            "mouse",
            "printer",
            "scanner",
            "joystick",
            "headset",
            "webcam",
            "usb",
            "bluetooth",
            "battery",
            "plug",
            "router",
            "modem",
            "projector",
            "smartwatch",
            "earbuds",
        ],
    ),
    (
        "document",
        "Document",
        [
            "file",
            "folder",
            "archive",
            "journal",
            "book",
            "newspaper",
            "clipboard",
            "document",
            "card-",
            "stickies",
            "sticky",
            "postcard",
            "receipt",
            "page",
        ],
    ),
    (
        "finance",
        "Finance",
        [
            "currency",
            "cash",
            "coin",
            "wallet",
            "credit-card",
            "bank",
            "piggy",
            "safe",
            "bag",
            "shop",
            "cart",
            "tag",
            "ticket",
            "percent",
            "receipt",
        ],
    ),
    (
        "geo",
        "Geo & Maps",
        [
            "geo",
            "map",
            "compass",
            "globe",
            "pin",
            "flag",
            "signpost",
            "location",
            "gps",
            "radar",
        ],
    ),
    (
        "people",
        "People",
        [
            "person",
            "people",
            "gender",
            "heart",
            "suit",
            "emoji",
            "hand",
            "finger",
            "eye",
            "ear",
            "nose",
        ],
    ),
    (
        "security",
        "Security",
        [
            "lock",
            "unlock",
            "shield",
            "key",
            "safe",
            "incognito",
            "eye-slash",
            "exclamation",
            "question",
            "ban",
            "slash",
        ],
    ),
    (
        "layout",
        "Layout",
        [
            "layout",
            "grid",
            "list",
            "view",
            "columns",
            "rows",
            "table",
            "panel",
            "sidebar",
            "stack",
            "window",
            "fullscreen",
            "aspect",
            "align",
            "justify",
            "indent",
            "hrule",
            "border",
        ],
    ),
    (
        "text",
        "Text & Editing",
        [
            "type",
            "text",
            "font",
            "bold",
            "italic",
            "underline",
            "subscript",
            "superscript",
            "paragraph",
            "list-ol",
            "list-ul",
            "blockquote",
            "code",
            "spellcheck",
            "pencil",
            "pen",
            "eraser",
            "scissors",
            "paint",
            "highlighter",
            "link",
            "unlink",
        ],
    ),
    (
        "shape",
        "Shapes",
        [
            "circle",
            "square",
            "triangle",
            "hexagon",
            "octagon",
            "diamond",
            "star",
            "heart-",
            "bounding-box",
            "plus",
            "dash",
            "x-",
        ],
    ),
    (
        "weather",
        "Weather",
        [
            "cloud",
            "sun",
            "moon",
            "snow",
            "wind",
            "umbrella",
            "thermometer",
            "droplet",
            "water",
            "fire",
            "lightning",
            "rainbow",
            "tornado",
        ],
    ),
    (
        "nature",
        "Nature",
        [
            "tree",
            "flower",
            "leaf",
            "bug",
            "egg",
            "fish",
            "bird",
            "paw",
            "feather",
            "mushroom",
        ],
    ),
    (
        "food",
        "Food & Drink",
        [
            "cup",
            "coffee",
            "cake",
            "cookie",
            "pizza",
            "apple",
            "basket",
            "bowl",
            "bread",
            "egg",
            "fork",
            "spoon",
            "knife",
        ],
    ),
    (
        "transport",
        "Transport",
        [
            "car",
            "bus",
            "train",
            "airplane",
            "bicycle",
            "scooter",
            "truck",
            "taxi",
            "ship",
            "boat",
            "rocket",
            "ev",
        ],
    ),
    (
        "tools",
        "Tools & Objects",
        [
            "tools",
            "hammer",
            "wrench",
            "gear",
            "screwdriver",
            "box",
            "bag",
            "briefcase",
            "suitcase",
            "backpack",
            "bucket",
            "easel",
            "palette",
            "scissors",
            "magnet",
            "funnel",
            "speedometer",
            "trophy",
            "award",
            "medal",
            "bandaid",
            "prescription",
            "hospital",
            "thermometer",
        ],
    ),
    (
        "interface",
        "Interface",
        [
            "search",
            "zoom",
            "plus-",
            "dash-",
            "x-",
            "check",
            "slash",
            "three-dots",
            "menu",
            "app",
            "toggle",
            "option",
            "switch",
            "input",
            "cursor",
            "hand-index",
            "hand-pointer",
            "hand-thumbs",
            "clipboard-check",
            "clipboard-x",
        ],
    ),
]

OTHER_CAT = ("other", "Other")


def fetch_css(url: str) -> str:
    print(f"Fetching {url} …", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "generate-icons-json/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def extract_names(css: str) -> list[str]:
    # Matches: .bi-some-name::before  (including compound: .bi-foo,.bi-bar::before)
    names = set()
    for m in re.finditer(r"\.bi-([\w-]+)::before", css):
        names.add(m.group(1))
    return sorted(names)


def categorise(names: list[str]) -> dict:
    cat_buckets: dict[str, list[str]] = {}
    other: list[str] = []

    for name in names:
        matched = False
        for cat_id, _label, keywords in CATEGORY_RULES:
            if any(kw in name for kw in keywords):
                cat_buckets.setdefault(cat_id, []).append(name)
                matched = True
                break
        if not matched:
            other.append(name)

    cat_buckets[OTHER_CAT[0]] = other

    categories = [
        {"id": c[0], "label": c[1]} for c in CATEGORY_RULES if c[0] in cat_buckets
    ]
    if other:
        categories.append({"id": OTHER_CAT[0], "label": OTHER_CAT[1]})

    return {"categories": categories, "icons": cat_buckets}


def main() -> None:
    try:
        css = fetch_css(CDN_URL)
    except Exception as exc:
        print(f"ERROR: could not fetch CSS — {exc}", file=sys.stderr)
        sys.exit(1)

    names = extract_names(css)
    print(f"Found {len(names)} icons.", flush=True)

    cats = categorise(names)

    payload = {
        "all": names,
        "categories": cats["categories"],
        "icons": cats["icons"],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"Written -> {OUTPUT}  ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
