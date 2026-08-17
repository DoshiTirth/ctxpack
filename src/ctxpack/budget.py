"""Token counting and budget-fitting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - fallback when tiktoken/model data unavailable
    _ENCODING = None


def count_tokens(text: str) -> int:
    """Estimate token count for `text`.

    Uses tiktoken's cl100k_base encoding when available; otherwise falls back
    to a conservative ~4-chars-per-token heuristic.
    """
    if _ENCODING is not None:
        return len(_ENCODING.encode(text, disallowed_special=()))
    return max(1, len(text) // 4)


@dataclass
class BudgetedFile:
    path: Path
    text: str
    tokens: int
    score: float


@dataclass
class BudgetResult:
    included: list[BudgetedFile]
    skipped: list[Path]
    total_tokens: int


def fit_to_budget(
    scored_files: list[tuple[Path, float]],
    read_text_fn,
    budget_tokens: int,
) -> BudgetResult:
    """Greedily include the highest-scored files until the token budget is spent.

    `read_text_fn` takes a Path and returns its text content (already decoded,
    already secret-scrubbed by the caller).
    """
    included: list[BudgetedFile] = []
    skipped: list[Path] = []
    total = 0

    for path, score in scored_files:
        text = read_text_fn(path)
        if text is None:
            skipped.append(path)
            continue

        tokens = count_tokens(text)
        if total + tokens > budget_tokens:
            skipped.append(path)
            continue

        included.append(BudgetedFile(path=path, text=text, tokens=tokens, score=score))
        total += tokens

    return BudgetResult(included=included, skipped=skipped, total_tokens=total)
