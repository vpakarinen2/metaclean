from __future__ import annotations

import subprocess
import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExifToolResult:
    stdout: str
    stderr: str
    exit_code: int

    def ok(self) -> bool:
        return self.exit_code == 0


def _run(cmd: list[str]) -> ExifToolResult:
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False,
    )
    return ExifToolResult(
        stdout=proc.stdout,
        stderr=proc.stderr,
        exit_code=proc.returncode,
    )


_EXIFTOOL_EXE: str | None = None


def _candidate_exiftool_exes() -> list[str]:
    candidates: list[str] = ["exiftool", "exiftool.exe"]
    repo_root_guess = Path(__file__).resolve().parents[2]
    local_dir = repo_root_guess / "exiftool"

    if local_dir.exists():
        local_exes = sorted(local_dir.glob("exiftool*.exe"))
        for p in local_exes:
            candidates.append(str(p))

    candidates.append(str(repo_root_guess / "exiftool.exe"))
    candidates.append(str(repo_root_guess / "exiftool(-k).exe"))

    return candidates


def _get_exiftool_exe() -> str:
    global _EXIFTOOL_EXE
    if _EXIFTOOL_EXE is not None:
        return _EXIFTOOL_EXE

    last_err: str | None = None
    for exe in _candidate_exiftool_exes():
        cmd = [exe, "-ver"]

        if ("/" in exe or "\\" in exe) and not Path(exe).exists():
            continue

        try:
            res = _run(cmd)
        except FileNotFoundError as e:
            last_err = str(e)
            continue

        if res.ok():
            _EXIFTOOL_EXE = exe
            return exe

        last_err = (res.stderr or res.stdout or "").strip()

    raise RuntimeError(
        "exiftool was not found or could not be executed. "
        "Make sure ExifTool is installed and `exiftool.exe` is on PATH, "
        "or ensure your local bundled exe is present (e.g. `exiftool(-k).exe`).\n"
        + (f"Last error: {last_err}" if last_err else "")
    )


def ensure_exiftool_available(exiftool_path: str | None = None) -> None:
    global _EXIFTOOL_EXE

    if exiftool_path is not None:
        p = Path(exiftool_path)
        if not p.exists() or not p.is_file():
            raise RuntimeError(f"--exiftool path does not exist or is not a file: {exiftool_path}")

        res = _run([str(p), "-ver"])
        if not res.ok():
            raise RuntimeError(
                f"exiftool override was provided but could not be executed: {p}\n"
                f"exit code: {res.exit_code}\n"
                f"stderr: {res.stderr.strip()}"
            )

        _EXIFTOOL_EXE = str(p)
        return

    _EXIFTOOL_EXE = None
    _EXIFTOOL_EXE = _get_exiftool_exe()


def view_as_text(path: Path, *, group_tags: bool) -> str:
    cmd = [_get_exiftool_exe()]
    if group_tags:
        cmd.append("-G1")
    cmd.extend(["-a", str(path)])

    res = _run(cmd)
    if not res.ok():
        raise RuntimeError(
            f"exiftool failed for {path} (exit code {res.exit_code}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"stderr: {res.stderr.strip()}"
        )

    return res.stdout.strip()


def view_as_json(path: Path, *, group_tags: bool) -> Any:
    cmd = [_get_exiftool_exe()]
    if group_tags:
        cmd.extend(["-G1", "-a"])
    else:
        cmd.append("-a")
    cmd.extend(["-j", str(path)])

    res = _run(cmd)
    if not res.ok():
        raise RuntimeError(
            f"exiftool failed for {path} (exit code {res.exit_code}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"stderr: {res.stderr.strip()}"
        )

    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse exiftool JSON output for {path}.") from e


def strip_all_metadata(path: Path) -> None:
    cmd = [_get_exiftool_exe(), "-all=", "-overwrite_original", str(path)]
    res = _run(cmd)
    if not res.ok():
        raise RuntimeError(
            f"exiftool failed to strip metadata for {path} (exit code {res.exit_code}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"stderr: {res.stderr.strip()}"
        )
