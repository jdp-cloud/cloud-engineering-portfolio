#!/usr/bin/env python3
"""
Flatten screenshot redactions, remove image metadata, and verify output hashes.

Examples:
  python3 sanitize-evidence.py \
    --input ../../../../assets/images/members/jacques-payne/phase-2/lab12c/evidence/02-terraform-apply-complete.png \
    --config evidence/redactions.json \
    --output ../../../../assets/images/members/jacques-payne/phase-2/lab12c/evidence/sanitized/02-terraform-apply-complete.png

  python3 sanitize-evidence.py \
    --input ../../../../assets/images/members/jacques-payne/phase-2/lab12c/evidence \
    --config evidence/redactions.json \
    --output ../../../../assets/images/members/jacques-payne/phase-2/lab12c/evidence/sanitized

Configuration format:
{
  "defaults": {
    "fill": "#000000",
    "padding": 0
  },
  "files": {
    "02-terraform-apply-complete.png": [
      {"x": 100, "y": 50, "width": 240, "height": 28}
    ]
  }
}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw
except ImportError as exc:
    raise SystemExit(
        "Pillow is required. Install it with:\n"
        "  python3 -m pip install Pillow"
    ) from exc


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}"
        ) from exc

    if not isinstance(data, dict):
        raise SystemExit("Configuration root must be a JSON object.")

    files = data.get("files", {})
    if not isinstance(files, dict):
        raise SystemExit('Configuration field "files" must be an object.')

    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        raise SystemExit('Configuration field "defaults" must be an object.')

    return data


def discover_inputs(input_path: Path) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise SystemExit(f"Unsupported image type: {input_path}")
        return [input_path]

    if input_path.is_dir():
        images = sorted(
            path
            for path in input_path.iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not images:
            raise SystemExit(f"No supported images found in: {input_path}")
        return images

    raise SystemExit(f"Input path does not exist: {input_path}")


def resolve_output_path(
    input_file: Path,
    input_root: Path,
    output_root: Path,
    multiple: bool,
) -> Path:
    if multiple or output_root.is_dir() or output_root.suffix == "":
        output_root.mkdir(parents=True, exist_ok=True)
        return output_root / input_file.name

    output_root.parent.mkdir(parents=True, exist_ok=True)
    return output_root


def parse_rectangle(
    item: dict[str, Any],
    image_width: int,
    image_height: int,
    padding: int,
) -> tuple[int, int, int, int]:
    required = ("x", "y", "width", "height")
    missing = [key for key in required if key not in item]
    if missing:
        raise ValueError(
            "Redaction rectangle is missing: " + ", ".join(missing)
        )

    x = int(item["x"]) - padding
    y = int(item["y"]) - padding
    width = int(item["width"]) + 2 * padding
    height = int(item["height"]) + 2 * padding

    if width <= 0 or height <= 0:
        raise ValueError("Redaction width and height must be positive.")

    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(image_width, x + width)
    y2 = min(image_height, y + height)

    if x1 >= x2 or y1 >= y2:
        raise ValueError(
            f"Redaction rectangle lies outside the image: {item}"
        )

    return x1, y1, x2, y2


def sanitize_image(
    input_file: Path,
    output_file: Path,
    rectangles: list[dict[str, Any]],
    fill: str,
    padding: int,
) -> None:
    with Image.open(input_file) as source:
        image = source.convert("RGBA")
        draw = ImageDraw.Draw(image)

        for item in rectangles:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Redaction entry must be an object: {item!r}"
                )
            box = parse_rectangle(
                item,
                image.width,
                image.height,
                padding,
            )
            draw.rectangle(box, fill=fill)

        # Rebuild a fresh image so original metadata and ancillary chunks
        # are not copied into the output.
        flattened = Image.new("RGBA", image.size)
        flattened.paste(image)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        suffix = output_file.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            flattened.convert("RGB").save(
                output_file,
                format="JPEG",
                quality=95,
                optimize=True,
            )
        elif suffix == ".webp":
            flattened.save(
                output_file,
                format="WEBP",
                quality=95,
                method=6,
            )
        else:
            flattened.save(
                output_file,
                format="PNG",
                optimize=True,
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Flatten screenshot redactions, strip metadata, and "
            "write sanitized image copies."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Input image or directory of images.",
    )
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="JSON file containing per-image redaction rectangles.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output image or output directory.",
    )
    parser.add_argument(
        "--allow-unconfigured",
        action="store_true",
        help=(
            "Re-encode images with no configured rectangles. "
            "Without this option, unconfigured files are skipped."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting existing output files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned operations without writing files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    defaults = config.get("defaults", {})
    configured_files = config.get("files", {})

    fill = str(defaults.get("fill", "#000000"))
    padding = int(defaults.get("padding", 0))

    input_files = discover_inputs(args.input)
    multiple = len(input_files) > 1 or args.input.is_dir()

    processed = 0
    skipped = 0

    for input_file in input_files:
        rectangles = configured_files.get(input_file.name)

        if rectangles is None:
            if not args.allow_unconfigured:
                print(f"SKIP  {input_file.name}: no configuration")
                skipped += 1
                continue
            rectangles = []

        if not isinstance(rectangles, list):
            raise SystemExit(
                f'Configuration for "{input_file.name}" must be a list.'
            )

        output_file = resolve_output_path(
            input_file,
            args.input,
            args.output,
            multiple,
        )

        try:
            same_file = (
                input_file.resolve() == output_file.resolve()
            )
        except FileNotFoundError:
            same_file = False

        if same_file and not args.overwrite:
            raise SystemExit(
                "Refusing to overwrite the input image. "
                "Choose another output path or pass --overwrite."
            )

        if output_file.exists() and not args.overwrite:
            raise SystemExit(
                f"Output already exists: {output_file}\n"
                "Pass --overwrite to replace it."
            )

        print(
            f"{'DRY' if args.dry_run else 'WRITE'} "
            f"{input_file.name} -> {output_file}"
        )
        print(f"      redactions: {len(rectangles)}")

        if args.dry_run:
            continue

        try:
            sanitize_image(
                input_file=input_file,
                output_file=output_file,
                rectangles=rectangles,
                fill=fill,
                padding=padding,
            )
        except (OSError, ValueError) as exc:
            raise SystemExit(
                f"Failed to sanitize {input_file}: {exc}"
            ) from exc

        print(f"      input_sha256:  {sha256_file(input_file)}")
        print(f"      output_sha256: {sha256_file(output_file)}")
        processed += 1

    print()
    print(f"Processed: {processed}")
    print(f"Skipped:   {skipped}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
