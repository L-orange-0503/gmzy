#!/usr/bin/env python3
"""Lossless image optimization for this static site.

PNG files are repacked with stronger zlib compression while preserving the
decoded PNG stream byte-for-byte. JPEG and GIF files are intentionally left
unchanged unless a dedicated lossless optimizer is installed; re-encoding
those formats could reduce visual quality.
"""

from __future__ import annotations

import argparse
import binascii
import os
import stat
import struct
import tempfile
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def read_png_chunks(data):
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")

    chunks = []
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG payload")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        chunks.append((kind, payload))
        offset = end
        if kind == b"IEND":
            break
    return chunks


def pack_png_chunk(kind, payload):
    crc = binascii.crc32(kind + payload) & 0xffffffff
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", crc)
    )


def atomic_write(path, data):
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def optimize_png(path, apply_changes):
    original = path.read_bytes()
    chunks = read_png_chunks(original)
    idat_payload = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
    if not idat_payload:
        raise ValueError("PNG has no IDAT data")

    decoded_stream = zlib.decompress(idat_payload)
    recompressed = zlib.compress(decoded_stream, level=9)
    if zlib.decompress(recompressed) != decoded_stream:
        raise ValueError("decoded PNG stream changed during recompression")

    optimized = bytearray(PNG_SIGNATURE)
    inserted_idat = False
    for kind, payload in chunks:
        if kind == b"IDAT":
            if not inserted_idat:
                optimized.extend(pack_png_chunk(b"IDAT", recompressed))
                inserted_idat = True
            continue
        optimized.extend(pack_png_chunk(kind, payload))

    optimized = bytes(optimized)
    if len(optimized) >= len(original):
        return "unchanged", len(original), len(original)

    if apply_changes:
        atomic_write(path, optimized)
        written = path.read_bytes()
        written_chunks = read_png_chunks(written)
        written_idat = b"".join(
            payload for kind, payload in written_chunks if kind == b"IDAT"
        )
        if zlib.decompress(written_idat) != decoded_stream:
            raise ValueError("post-write PNG verification failed")

    return "optimized", len(original), len(optimized)


def process_file(path, apply_changes):
    suffix = path.suffix.lower()
    if suffix == ".png":
        return optimize_png(path, apply_changes)
    return "skipped", path.stat().st_size, path.stat().st_size


def format_size(size):
    units = ("B", "KB", "MB", "GB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024


def main():
    parser = argparse.ArgumentParser(
        description="Repack PNG files losslessly and audit other image formats."
    )
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write optimized files; without this flag the command is a dry run",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    excluded = {".git", "node_modules", ".cache", "dist", "build"}
    paths = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_SUFFIXES
        and not any(part in excluded for part in path.parts)
    )

    counts = {"optimized": 0, "unchanged": 0, "skipped": 0, "failed": 0}
    saved = 0
    for path in paths:
        relative = path.relative_to(root)
        try:
            status, before, after = process_file(path, args.apply)
            counts[status] += 1
            saved += before - after
            if status == "optimized":
                action = "optimized" if args.apply else "would optimize"
                print(f"{relative}: {action}, {format_size(before)} -> {format_size(after)}")
            elif status == "skipped":
                print(f"{relative}: skipped (no safe lossless encoder for {path.suffix.lower()})")
            else:
                print(f"{relative}: unchanged")
        except Exception as error:
            counts["failed"] += 1
            print(f"{relative}: FAILED ({error})")

    mode = "applied" if args.apply else "dry run"
    print(
        f"\n{mode}: {len(paths)} image(s), "
        f"{counts['optimized']} optimized, {counts['unchanged']} unchanged, "
        f"{counts['skipped']} skipped, {counts['failed']} failed; "
        f"space change: {format_size(saved)}"
    )
    return 1 if counts["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
