"""Generate the deterministic diagram used by the bundled example."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "examples" / "master-thesis" / "architecture.png"
WIDTH = 900
HEIGHT = 260


def _chunk(kind: bytes, payload: bytes) -> bytes:
    content = kind + payload
    return struct.pack(">I", len(payload)) + content + struct.pack(">I", zlib.crc32(content))


def _pixel(x: int, y: int) -> tuple[int, int, int]:
    boxes = ((40, 230), (335, 565), (670, 860))
    for left, right in boxes:
        if left <= x <= right and 50 <= y <= 210:
            if x in {left, right} or y in {50, 210}:
                return (25, 55, 95)
            return (225, 237, 248)
    if 230 < x < 335 and 125 <= y <= 135:
        return (25, 55, 95)
    if 565 < x < 670 and 125 <= y <= 135:
        return (25, 55, 95)
    return (255, 255, 255)


def main() -> None:
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        for x in range(WIDTH):
            raw.extend(_pixel(x, y))
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png = signature + _chunk(b"IHDR", header) + _chunk(b"IDAT", zlib.compress(raw, 9))
    png += _chunk(b"IEND", b"")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(png)


if __name__ == "__main__":
    main()
