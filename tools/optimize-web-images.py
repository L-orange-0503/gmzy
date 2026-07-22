#!/usr/bin/env python3
"""Optimize image assets referenced by the static site without breaking Pages paths.

JPEG files are re-encoded through macOS ``sips`` at a configurable high quality
setting. A result is accepted only when it is smaller, still decodes as JPEG,
and has the original dimensions. PNGs with transparency are losslessly repacked;
opaque PNGs can be converted to JPEG while retaining their relative asset path
in the HTML/CSS references.
"""

from __future__ import annotations

import argparse
import binascii
import os
import re
import shutil
import stat
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}
HTML_ATTR_ASSET = re.compile(r"\b(?:src|href)\s*=\s*([\"'])([^\"']+)\1", re.IGNORECASE)
CSS_URL_ASSET = re.compile(r"url\(\s*([\"']?)([^\"')]+)\1\s*\)", re.IGNORECASE)


def read_png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")
    chunks: list[tuple[bytes, bytes]] = []
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


def pack_png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def png_has_transparency(chunks: list[tuple[bytes, bytes]]) -> bool:
    header = next((payload for kind, payload in chunks if kind == b"IHDR"), None)
    if header is None or len(header) != 13:
        raise ValueError("PNG has no valid IHDR")
    color_type = header[9]
    return color_type in {4, 6} or any(kind == b"tRNS" for kind, _ in chunks)


def losslessly_repack_png(source: Path) -> tuple[bytes, bytes]:
    original = source.read_bytes()
    chunks = read_png_chunks(original)
    compressed = b"".join(payload for kind, payload in chunks if kind == b"IDAT")
    if not compressed:
        raise ValueError("PNG has no IDAT payload")
    decoded = zlib.decompress(compressed)
    replacement = zlib.compress(decoded, level=9)
    if zlib.decompress(replacement) != decoded:
        raise ValueError("PNG decoded stream changed")

    result = bytearray(PNG_SIGNATURE)
    added_idat = False
    for kind, payload in chunks:
        if kind == b"IDAT":
            if not added_idat:
                result.extend(pack_png_chunk(b"IDAT", replacement))
                added_idat = True
            continue
        result.extend(pack_png_chunk(kind, payload))
    return original, bytes(result)


def read_image_info(source: Path) -> tuple[str, int, int, bool]:
    completed = subprocess.run(
        ["sips", "-g", "format", "-g", "pixelWidth", "-g", "pixelHeight", "-g", "hasAlpha", str(source)],
        check=True,
        text=True,
        capture_output=True,
    )
    values: dict[str, str] = {}
    for line in completed.stdout.splitlines()[1:]:
        if ":" in line:
            key, value = line.strip().split(":", 1)
            values[key.strip()] = value.strip()
    return (
        values["format"].lower(),
        int(values["pixelWidth"]),
        int(values["pixelHeight"]),
        values.get("hasAlpha", "no").lower() == "yes",
    )


def render_jpeg(source: Path, destination: Path, quality: int) -> None:
    subprocess.run(
        [
            "sips", "--setProperty", "format", "jpeg", "--setProperty", "formatOptions", str(quality),
            "--out", str(destination), str(source),
        ],
        check=True,
        text=True,
        capture_output=True,
    )


def atomic_write(path: Path, data: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def site_image_paths(root: Path, index: Path) -> list[Path]:
    content = index.read_text(encoding="utf-8")
    candidates = [match.group(2) for match in HTML_ATTR_ASSET.finditer(content)]
    candidates.extend(match.group(2) for match in CSS_URL_ASSET.finditer(content))
    images: set[Path] = set()
    for value in candidates:
        if not value.startswith("./assets/"):
            continue
        asset = (root / value.removeprefix("./")).resolve()
        if root not in asset.parents or asset.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if not asset.is_file():
            raise FileNotFoundError(f"referenced image is missing: {value}")
        images.add(asset)
    return sorted(images)


def backup_original(source: Path, root: Path, backup_root: Path) -> Path:
    destination = backup_root / source.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def format_bytes(size: int) -> str:
    return f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--index", type=Path, default=Path("index.html"))
    parser.add_argument("--quality", type=int, default=94, choices=range(92, 96))
    parser.add_argument("--backup-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    index = (root / args.index).resolve()
    if root not in index.parents or not index.is_file():
        raise ValueError("index must be a file inside root")
    if args.apply and args.backup_root is None:
        raise ValueError("--apply requires --backup-root so originals remain recoverable")
    backup_root = args.backup_root.resolve() if args.backup_root else None

    images = site_image_paths(root, index)
    print(f"referenced web images: {len(images)}")
    changed = 0
    unchanged = 0
    saved = 0
    with tempfile.TemporaryDirectory(prefix="site-image-optimization-") as temp_dir:
        temporary = Path(temp_dir)
        for source in images:
            relative = source.relative_to(root)
            suffix = source.suffix.lower()
            before = source.stat().st_size
            if suffix == ".png":
                original, candidate = losslessly_repack_png(source)
                if png_has_transparency(read_png_chunks(original)):
                    if len(candidate) >= len(original):
                        print(f"{relative}: transparent PNG unchanged ({format_bytes(before)})")
                        unchanged += 1
                        continue
                    if args.apply:
                        backup_original(source, root, backup_root)
                        atomic_write(source, candidate)
                    changed += 1
                    saved += len(original) - len(candidate)
                    print(f"{relative}: transparent PNG lossless {format_bytes(before)} -> {format_bytes(len(candidate))}")
                    continue

                candidate_path = temporary / f"{source.stem}.jpg"
                render_jpeg(source, candidate_path, args.quality)
                format_name, width, height, has_alpha = read_image_info(candidate_path)
                old_format, old_width, old_height, _ = read_image_info(source)
                if format_name != "jpeg" or has_alpha or (width, height) != (old_width, old_height):
                    raise ValueError(f"opaque PNG conversion validation failed: {relative}")
                after = candidate_path.stat().st_size
                if after >= before:
                    print(f"{relative}: opaque PNG kept (JPEG candidate not smaller: {format_bytes(before)} -> {format_bytes(after)})")
                    unchanged += 1
                    continue
                if args.apply:
                    backup_original(source, root, backup_root)
                    target = source.with_suffix(".jpg")
                    if target.exists():
                        raise FileExistsError(f"refusing to replace existing target: {target}")
                    shutil.copy2(candidate_path, target)
                    text = index.read_text(encoding="utf-8")
                    updated = text.replace(f"./{relative.as_posix()}", f"./{target.relative_to(root).as_posix()}")
                    if updated == text:
                        raise ValueError(f"PNG had no replaceable HTML/CSS reference: {relative}")
                    atomic_write(index, updated.encode("utf-8"))
                changed += 1
                saved += before - after
                print(f"{relative}: opaque PNG -> JPEG {format_bytes(before)} -> {format_bytes(after)}")
                continue

            candidate_path = temporary / source.name
            render_jpeg(source, candidate_path, args.quality)
            format_name, width, height, has_alpha = read_image_info(candidate_path)
            old_format, old_width, old_height, old_alpha = read_image_info(source)
            if (format_name, width, height, has_alpha) != ("jpeg", old_width, old_height, False):
                raise ValueError(f"JPEG validation failed: {relative}")
            after = candidate_path.stat().st_size
            if after >= before:
                print(f"{relative}: kept ({format_bytes(before)}; Q{args.quality} candidate {format_bytes(after)} is not smaller)")
                unchanged += 1
                continue
            if args.apply:
                backup_original(source, root, backup_root)
                shutil.copy2(candidate_path, source)
            changed += 1
            saved += before - after
            print(f"{relative}: JPEG Q{args.quality} {format_bytes(before)} -> {format_bytes(after)}")

    print(f"result: {changed} changed, {unchanged} retained, saved {format_bytes(saved)}")
    if not args.apply:
        print("dry run: no project files changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
