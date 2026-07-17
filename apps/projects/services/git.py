"""Estado de Git en modo lectura, usando comandos git nativos."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

_TIMEOUT = 5


@dataclass(frozen=True)
class GitStatus:
    is_repo: bool
    branch: str = ""
    is_dirty: bool = False
    ahead: int = 0
    behind: int = 0
    has_upstream: bool = False


def _run(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=path,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
    )


def get_status(path: Path) -> GitStatus:
    """Devuelve el estado actual de Git del repositorio en ``path``."""
    if not (path / ".git").exists():
        return GitStatus(is_repo=False)

    branch = _run(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    is_dirty = bool(_run(path, "status", "--porcelain").stdout.strip())

    ahead = behind = 0
    counts = _run(path, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    has_upstream = counts.returncode == 0
    if has_upstream:
        parts = counts.stdout.split()
        if len(parts) == 2:
            behind, ahead = int(parts[0]), int(parts[1])

    return GitStatus(
        is_repo=True,
        branch=branch,
        is_dirty=is_dirty,
        ahead=ahead,
        behind=behind,
        has_upstream=has_upstream,
    )
