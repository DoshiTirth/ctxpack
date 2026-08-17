"""Walk a repository, respecting .gitignore and additional ignore patterns."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import pathspec

DEFAULT_IGNORES = [
    ".git/",
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    ".venv/",
    "venv/",
    "dist/",
    "build/",
    "*.egg-info/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    "*.lock",
    "*.min.js",
    "*.map",
]

# Extensions we never try to read as text.
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".mov", ".avi", ".wav",
    ".db", ".sqlite", ".sqlite3",
    ".pyc", ".pyo",
}


@dataclass
class WalkOptions:
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    respect_gitignore: bool = True
    follow_symlinks: bool = False


def _load_gitignore_spec(root: Path) -> pathspec.PathSpec:
    patterns = list(DEFAULT_IGNORES)
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        patterns.extend(gitignore_path.read_text(errors="ignore").splitlines())
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def walk_repo(root: str | Path, options: WalkOptions | None = None) -> list[Path]:
    """Return a list of file paths under `root`, filtered by ignore rules.

    Paths are returned relative to `root`.
    """
    options = options or WalkOptions()
    root = Path(root).resolve()

    spec = (
        _load_gitignore_spec(root)
        if options.respect_gitignore
        else pathspec.PathSpec.from_lines("gitwildmatch", DEFAULT_IGNORES)
    )
    include_spec = (
        pathspec.PathSpec.from_lines("gitwildmatch", options.include_globs)
        if options.include_globs
        else None
    )
    exclude_spec = (
        pathspec.PathSpec.from_lines("gitwildmatch", options.exclude_globs)
        if options.exclude_globs
        else None
    )

    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=options.follow_symlinks):
        rel_dir = Path(dirpath).relative_to(root)

        # Prune ignored directories in-place so os.walk doesn't descend into them.
        kept_dirs = []
        for d in dirnames:
            rel_d = str((rel_dir / d).as_posix()) + "/"
            if rel_dir == Path("."):
                rel_d = d + "/"
            if spec.match_file(rel_d):
                continue
            kept_dirs.append(d)
        dirnames[:] = kept_dirs

        for f in filenames:
            rel_path = rel_dir / f if rel_dir != Path(".") else Path(f)
            rel_str = rel_path.as_posix()

            if spec.match_file(rel_str):
                continue
            if exclude_spec and exclude_spec.match_file(rel_str):
                continue
            if include_spec and not include_spec.match_file(rel_str):
                continue
            if Path(f).suffix.lower() in BINARY_EXTENSIONS:
                continue

            results.append(rel_path)

    return sorted(results)
