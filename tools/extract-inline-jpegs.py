#!/usr/bin/env python3
"""Extract inline JPEG data URIs from a static HTML page into local assets.

The transformation preserves the original JPEG bytes. It only replaces each
``src="data:image/jpeg;base64,..."`` value with an HTML-document-relative
asset path, which keeps the result portable for GitHub Pages project sites.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path


IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_DATA_JPEG = re.compile(
    r"(\bsrc\s*=\s*)([\"'])(data:image/jpeg;base64,([^\"']+))\2",
    re.IGNORECASE,
)
CLASS_ATTR = re.compile(r"\bclass\s*=\s*([\"'])(.*?)\1", re.IGNORECASE)
ALT_ATTR = re.compile(r"\balt\s*=\s*([\"'])(.*?)\1", re.IGNORECASE)


@dataclass(frozen=True)
class InlineImage:
    number: int
    category: str
    relative_target: str
    alt: str
    width: int
    height: int
    jpeg: bytes


def read_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    """Read dimensions from a valid JPEG Start Of Frame marker."""
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise ValueError("invalid JPEG start or end marker")

    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }
    offset = 2
    while offset < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        segment_length = int.from_bytes(data[offset:offset + 2], "big")
        if segment_length < 2 or offset + segment_length > len(data):
            break
        if marker in sof_markers:
            if segment_length < 8:
                break
            height = int.from_bytes(data[offset + 3:offset + 5], "big")
            width = int.from_bytes(data[offset + 5:offset + 7], "big")
            if width and height:
                return width, height
        offset += segment_length
    raise ValueError("JPEG dimensions were not found")


def attribute_value(pattern: re.Pattern[str], tag: str) -> str:
    match = pattern.search(tag)
    return match.group(2) if match else ""


def categorize(tag: str, counters: dict[str, int]) -> tuple[str, str]:
    classes = set(attribute_value(CLASS_ATTR, tag).split())
    if "course-cover" in classes:
        category = "course"
        filename = f"course-{counters[category]:02}.jpg"
    elif "simulation-cover" in classes:
        category = "simulation"
        filename = f"simulation-{counters[category]:02}.jpg"
    else:
        category = "exhibition"
        filename = (
            "virtual-exhibition.jpg"
            if counters[category] == 1
            else f"exhibition-{counters[category]:02}.jpg"
        )
    return category, filename


def collect_images(html: str, asset_dir: Path) -> list[InlineImage]:
    counters = {"course": 0, "simulation": 0, "exhibition": 0}
    images: list[InlineImage] = []
    for tag_match in IMG_TAG.finditer(html):
        tag = tag_match.group(0)
        source_match = SRC_DATA_JPEG.search(tag)
        if not source_match:
            continue
        classes = set(attribute_value(CLASS_ATTR, tag).split())
        category_key = (
            "course" if "course-cover" in classes
            else "simulation" if "simulation-cover" in classes
            else "exhibition"
        )
        counters[category_key] += 1
        category, filename = categorize(tag, counters)
        try:
            jpeg = base64.b64decode(source_match.group(4), validate=True)
        except binascii.Error as error:
            raise ValueError(f"image {len(images) + 1} has invalid Base64") from error
        width, height = read_jpeg_dimensions(jpeg)
        images.append(
            InlineImage(
                number=len(images) + 1,
                category=category,
                relative_target=f"./{asset_dir.as_posix()}/{filename}",
                alt=attribute_value(ALT_ATTR, tag),
                width=width,
                height=height,
                jpeg=jpeg,
            )
        )

    expected = {"course": 8, "simulation": 8, "exhibition": 1}
    if counters != expected:
        raise ValueError(f"unexpected inline JPEG categories: {counters}; expected {expected}")
    if len(images) != 17:
        raise ValueError(f"expected 17 inline JPEGs, found {len(images)}")
    return images


def replace_sources(html: str, images: list[InlineImage]) -> str:
    replacements = iter(images)

    def replace_tag(tag_match: re.Match[str]) -> str:
        tag = tag_match.group(0)
        if not SRC_DATA_JPEG.search(tag):
            return tag
        image = next(replacements)
        return SRC_DATA_JPEG.sub(
            lambda match: f'{match.group(1)}{match.group(2)}{image.relative_target}{match.group(2)}',
            tag,
            count=1,
        )

    updated = IMG_TAG.sub(replace_tag, html)
    try:
        next(replacements)
    except StopIteration:
        pass
    else:
        raise ValueError("not every inline image received a replacement")
    if "data:image/jpeg;base64," in updated.lower():
        raise ValueError("an inline JPEG data URI remained after replacement")
    return updated


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=Path("index.html"))
    parser.add_argument("--asset-dir", type=Path, default=Path("assets/inline-covers"))
    parser.add_argument("--apply", action="store_true", help="write assets and update the HTML file")
    args = parser.parse_args()

    html_path = args.html.resolve()
    root = html_path.parent
    asset_dir = args.asset_dir
    if asset_dir.is_absolute() or ".." in asset_dir.parts:
        raise ValueError("asset directory must be a project-relative path")
    source = html_path.read_text(encoding="utf-8")
    images = collect_images(source, asset_dir)
    updated = replace_sources(source, images)

    for image in images:
        digest = hashlib.sha256(image.jpeg).hexdigest()[:12]
        print(
            f"{image.number:02d} {image.category:10} {image.width}x{image.height} "
            f"{len(image.jpeg):7} B {image.relative_target} sha256:{digest} alt={image.alt!r}"
        )
    print(f"\ninline HTML bytes: {len(source):,} -> {len(updated):,}")
    print(f"extracted JPEG bytes: {sum(len(image.jpeg) for image in images):,}")

    if not args.apply:
        print("dry run: no files changed")
        return 0

    for image in images:
        target = root / image.relative_target.removeprefix("./")
        if target.exists() and target.read_bytes() != image.jpeg:
            raise ValueError(f"refusing to overwrite a different file: {target}")
        if not target.exists():
            atomic_write(target, image.jpeg)

    atomic_write(html_path, updated.encode("utf-8"))
    print("applied: 17 JPEG assets written and HTML sources updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
