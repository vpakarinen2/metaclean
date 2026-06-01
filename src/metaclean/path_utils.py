from __future__ import annotations

from collections import Counter
from typing import Iterable
from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _build_output_name(input_path: Path, *, suffix: str | None, collision: bool) -> str:
    stem = input_path.stem
    ext = input_path.suffix

    if suffix is not None:
        return f"{stem}{suffix}{ext}"

    if collision:
        return f"{stem}_cleaned{ext}"

    return input_path.name


def compute_output_paths(
    inputs: Iterable[Path],
    *,
    output_dir: Path,
    suffix: str | None,
) -> dict[Path, Path]:
    inputs_list = list(inputs)
    collisions = Counter(p.name for p in inputs_list)

    out: dict[Path, Path] = {}
    for p in inputs_list:
        out_name = _build_output_name(
            p,
            suffix=suffix,
            collision=collisions[p.name] > 1,
        )
        out[p] = output_dir / out_name
    return out
