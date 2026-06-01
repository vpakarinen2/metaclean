from __future__ import annotations

import argparse
import shutil
import json
import sys

from typing import Sequence
from pathlib import Path

from .exiftool import ensure_exiftool_available, strip_all_metadata, view_as_json, view_as_text
from .path_utils import compute_output_paths, ensure_dir


def _iter_existing_files(paths: Sequence[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            raise FileNotFoundError(str(p))
        if not p.is_file():
            raise ValueError(f"Not a file: {p}")
        out.append(p)
    return out


def _cmd_view(args: argparse.Namespace) -> int:
    files = _iter_existing_files(args.files)
    ensure_exiftool_available(args.exiftool)

    if args.json:
        if len(files) == 1:
            meta = view_as_json(files[0], group_tags=args.group_tags)
            print(json.dumps(meta, ensure_ascii=False, indent=2))
            return 0

        wrapper = {}
        for f in files:
            wrapper[str(f)] = view_as_json(f, group_tags=args.group_tags)
        print(json.dumps(wrapper, ensure_ascii=False, indent=2))
        return 0

    for i, f in enumerate(files):
        if i > 0:
            print("\n" + "=" * 80 + "\n")
        print(view_as_text(f, group_tags=args.group_tags))
    return 0


def _cmd_clean(args: argparse.Namespace) -> int:
    inputs = _iter_existing_files(args.files)
    ensure_exiftool_available(args.exiftool)

    output_dir_value: str | None = getattr(args, "output_dir", None)
    if output_dir_value is None:
        output_dir_value = "output"

    output_dir = Path(output_dir_value)
    ensure_dir(output_dir)

    output_paths = compute_output_paths(
        inputs,
        output_dir=output_dir,
        suffix=args.suffix,
    )

    any_failed = False

    for inp in inputs:
        out_path = output_paths[inp]

        if args.dry_run:
            print(f"COPY: {inp} -> {out_path}")
            print(f"RUN: exiftool -all= -overwrite_original {out_path}")
            continue

        try:
            shutil.copy2(inp, out_path)
            strip_all_metadata(out_path)
            print(f"OK: {inp} -> {out_path}")
        except Exception as e:
            any_failed = True
            print(f"ERROR: Failed to clean {inp}: {e}", file=sys.stderr)

    return 1 if any_failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="metaclean",
        description="View and remove metadata from images and videos.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    view_p = subparsers.add_parser("view", help="View metadata")
    view_p.add_argument("files", nargs="+", help="Input image/video files")
    view_p.add_argument("--json", action="store_true", help="Output JSON")
    view_p.add_argument(
        "--group-tags",
        action="store_true",
        help="Group tags when producing output.",
    )
    view_p.set_defaults(func=_cmd_view)
    view_p.add_argument(
        "--exiftool",
        default=None,
        dest="exiftool",
        help="Path to exiftool.exe to use (overrides PATH and local ./exiftool).",
    )

    clean_p = subparsers.add_parser("clean", help="Remove metadata (creates cleaned copies)")
    clean_p.add_argument("files", nargs="+", help="Input image/video files")
    clean_p.add_argument(
        "--output-dir",
        default=None,
        dest="output_dir",
        help="Directory to write cleaned copies (default: output).",
    )
    clean_p.add_argument(
        "--output",
        default=None,
        dest="output_dir",
        help="Alias for --output-dir.",
    )
    clean_p.add_argument(
        "--suffix",
        default=None,
        help="Suffix inserted between filename stem and extension (e.g. _cleaned). "
        "If omitted, a '_cleaned' suffix is added only when input basenames collide.",
    )
    clean_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print copy + exiftool commands without writing anything.",
    )
    clean_p.add_argument(
        "--exiftool",
        default=None,
        dest="exiftool",
        help="Path to exiftool.exe to use (overrides PATH and local ./exiftool).",
    )
    clean_p.set_defaults(func=_cmd_clean)

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(list(argv))

    try:
        rc = args.func(args)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        rc = 2

    raise SystemExit(rc)
