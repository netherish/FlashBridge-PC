from __future__ import annotations

import hashlib
from pathlib import Path


def format_size(num_bytes: int | float) -> str:
    size = float(num_bytes)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0 or unit == "TiB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TiB"


def file_size(path: str | Path) -> int:
    return Path(path).stat().st_size


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def shorten(text: str, limit: int = 120) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def safe_filename(text: str) -> str:
    invalid = '<>:"/\\|?*'
    return "".join("_" if ch in invalid or ord(ch) < 32 else ch for ch in text).strip()
