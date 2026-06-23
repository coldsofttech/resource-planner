#!/usr/bin/env python3
"""
Generate apps/web/static/images/favicon.ico for Resource Planner.

Produces a 16x16 and 32x32 ICO with a rounded-square gradient background
and white "RP" letters, matching the brand colours in tokens.css.

No third-party dependencies — pure stdlib only.
"""

import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Brand colours approximated from tokens.css oklch values:
#   --rp-accent: oklch(0.55 0.18 270)  →  #5B59D6  (indigo)
#   purple:      oklch(0.55 0.18 305)  →  #8B47C4  (violet)
ACCENT = (0x5B, 0x59, 0xD6)
PURPLE = (0x8B, 0x47, 0xC4)


# ---------------------------------------------------------------------------
# Pixel-font glyphs for "R" and "P"  (3 wide × 5 tall, MSB = leftmost pixel)
# ---------------------------------------------------------------------------
GLYPH: dict[str, list[int]] = {
    "R": [0b111, 0b101, 0b110, 0b101, 0b101],
    "P": [0b110, 0b101, 0b110, 0b100, 0b100],
}
GLYPH_W, GLYPH_H = 3, 5


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(x: int, y: int, size: int) -> tuple:
    """135° linear gradient (top-left → bottom-right)."""
    t = (x + y) / max(1, (size - 1) * 2)
    return _lerp(ACCENT, PURPLE, t)


def _in_rounded_rect(x: int, y: int, size: int, radius: int) -> bool:
    dx = max(0, max(radius - x, x - (size - 1 - radius)))
    dy = max(0, max(radius - y, y - (size - 1 - radius)))
    return dx * dx + dy * dy <= radius * radius


def _draw_glyph(
    canvas: list[list[int]], size: int, glyph: list[int], ox: int, oy: int, scale: int
) -> None:
    for gy in range(GLYPH_H):
        row = glyph[gy]
        for gx in range(GLYPH_W):
            if (row >> (GLYPH_W - 1 - gx)) & 1:
                for dy in range(scale):
                    for dx in range(scale):
                        px, py = ox + gx * scale + dx, oy + gy * scale + dy
                        if 0 <= px < size and 0 <= py < size:
                            canvas[py][px] = 2  # white letter


def _render(size: int) -> list[list[tuple]]:
    """Return a size×size list of (R,G,B,A) tuples."""
    # 0 = transparent, 1 = gradient bg, 2 = white
    canvas: list[list[int]] = [[0] * size for _ in range(size)]
    radius = max(2, size // 5)

    # Background rounded rectangle
    for y in range(size):
        for x in range(size):
            if _in_rounded_rect(x, y, size, radius):
                canvas[y][x] = 1

    # Letters
    if size <= 16:
        # Scale 1: glyphs 3×5, gap 1 → total 7×5
        gap = 1
        total_w = GLYPH_W + gap + GLYPH_W  # 7
        ox = (size - total_w) // 2
        oy = (size - GLYPH_H) // 2 + 1
        _draw_glyph(canvas, size, GLYPH["R"], ox, oy, 1)
        _draw_glyph(canvas, size, GLYPH["P"], ox + GLYPH_W + gap, oy, 1)
    else:
        # Scale 2: glyphs 6×10, gap 2 → total 14×10
        scale = 2
        gap = 2
        total_w = GLYPH_W * scale + gap + GLYPH_W * scale  # 14
        ox = (size - total_w) // 2
        oy = (size - GLYPH_H * scale) // 2 + 1
        _draw_glyph(canvas, size, GLYPH["R"], ox, oy, scale)
        _draw_glyph(canvas, size, GLYPH["P"], ox + GLYPH_W * scale + gap, oy, scale)

    # Map markers to RGBA
    rgba: list[list[tuple]] = []
    for y in range(size):
        row: list[tuple] = []
        for x in range(size):
            p = canvas[y][x]
            if p == 0:
                row.append((0, 0, 0, 0))
            elif p == 1:
                r, g, b = _gradient(x, y, size)
                row.append((r, g, b, 255))
            else:
                row.append((255, 255, 255, 255))
        rgba.append(row)
    return rgba


def _bmp_image(size: int, rgba: list[list[tuple]]) -> bytes:
    """Build a BMP DIB (no file header) suitable for embedding in ICO."""
    header = struct.pack(
        "<IiiHHIIiiII",
        40,  # biSize
        size,  # biWidth
        size * 2,  # biHeight (doubled per ICO spec)
        1,  # biPlanes
        32,  # biBitCount
        0,
        0,  # biCompression, biSizeImage
        0,
        0,  # pixels-per-metre
        0,
        0,  # biClrUsed, biClrImportant
    )

    # XOR mask: BGRA, bottom-up
    xor = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = rgba[y][x]
            xor.extend([b, g, r, a])

    # AND mask: 1 bit per pixel (0=opaque, 1=transparent), rows padded to 4 bytes
    row_bytes = ((size + 31) // 32) * 4
    and_mask = bytearray()
    for y in range(size - 1, -1, -1):
        row = bytearray(row_bytes)
        for x in range(size):
            if rgba[y][x][3] == 0:
                row[x // 8] |= 1 << (7 - x % 8)
        and_mask.extend(row)

    return header + bytes(xor) + bytes(and_mask)


def build_ico(sizes: list[int]) -> bytes:
    images = [_bmp_image(s, _render(s)) for s in sizes]
    n = len(images)
    dir_size = 6 + 16 * n
    offsets: list[int] = []
    pos = dir_size
    for img in images:
        offsets.append(pos)
        pos += len(img)

    ico = struct.pack("<HHH", 0, 1, n)
    for size, img, off in zip(sizes, images, offsets, strict=True):
        ico += struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(img), off)
    for img in images:
        ico += img
    return ico


if __name__ == "__main__":
    out = ROOT / "apps" / "web" / "static" / "images" / "favicon.ico"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_ico([16, 32])
    out.write_bytes(data)
    print(f"Generated {out}  ({len(data):,} bytes)")
