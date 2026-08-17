"""Rank files by relevance so the highest-value files get first claim on the token budget."""

from __future__ import annotations

import subprocess
from pathlib import Path

# Files that are almost always high-signal for understanding a codebase.
PRIORITY_NAMES = {
    "readme.md", "readme.rst", "readme.txt",
    "pyproject.toml", "package.json", "cargo.toml", "go.mod",
    "setup.py", "makefile", "dockerfile",
}

PRIORITY_EXTENSIONS_BOOST = {
    ".py": 1.0, ".ts": 1.0, ".tsx": 1.0, ".js": 0.9, ".jsx": 0.9,
    ".go": 1.0, ".rs": 1.0, ".java": 0.9, ".rb": 0.9, ".c": 0.9, ".cpp": 0.9,
    ".md": 0.6, ".yml": 0.4, ".yaml": 0.4, ".json": 0.3, ".toml": 0.4,
}

TEST_DIR_PENALTY = 0.3
LOCK_OR_GENERATED_PENALTY = 0.1


def _git_recency_scores(root: Path, paths: list[Path]) -> dict[Path, float]:
    """Score files by how recently/often they've changed, via git log.

    Falls back to a uniform score if git isn't available or root isn't a repo.
    """
    scores: dict[Path, float] = {p: 0.0 for p in paths}
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", "--name-only", "--pretty=format:", "-n", "500"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return scores

    if result.returncode != 0:
        return scores

    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        counts[line] = counts.get(line, 0) + 1

    if not counts:
        return scores

    max_count = max(counts.values())
    for p in paths:
        c = counts.get(p.as_posix(), 0)
        scores[p] = c / max_count if max_count else 0.0

    return scores


def rank_files(root: str | Path, paths: list[Path]) -> list[tuple[Path, float]]:
    """Return (path, score) pairs sorted descending by relevance score in [0, ~2.5]."""
    root = Path(root)
    recency = _git_recency_scores(root, paths)

    scored: list[tuple[Path, float]] = []
    for p in paths:
        name_lower = p.name.lower()
        ext = p.suffix.lower()

        score = 0.0
        if name_lower in PRIORITY_NAMES:
            score += 1.2
        score += PRIORITY_EXTENSIONS_BOOST.get(ext, 0.2)
        score += recency.get(p, 0.0)

        parts_lower = [part.lower() for part in p.parts]
        if any(part in {"test", "tests", "__tests__", "spec"} for part in parts_lower):
            score *= TEST_DIR_PENALTY + 1  # tests still matter, just less than source
            score -= TEST_DIR_PENALTY
        if "generated" in parts_lower or name_lower.endswith(".lock"):
            score *= LOCK_OR_GENERATED_PENALTY

        scored.append((p, max(score, 0.0)))

    return sorted(scored, key=lambda item: item[1], reverse=True)
