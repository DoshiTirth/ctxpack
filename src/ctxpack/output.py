"""Render a BudgetResult as Markdown or JSON."""

from __future__ import annotations

import json

from .budget import BudgetResult

_LANG_HINTS = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "tsx",
    ".jsx": "jsx", ".go": "go", ".rs": "rust", ".java": "java", ".rb": "ruby",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".sh": "bash",
    ".yml": "yaml", ".yaml": "yaml", ".json": "json", ".toml": "toml",
    ".md": "markdown", ".sql": "sql", ".html": "html", ".css": "css",
}


def to_markdown(result: BudgetResult, root_label: str) -> str:
    lines = [
        f"# Context bundle: {root_label}",
        "",
        f"Included {len(result.included)} files, "
        f"{len(result.skipped)} skipped, "
        f"~{result.total_tokens} tokens.",
        "",
    ]

    for f in result.included:
        lang = _LANG_HINTS.get(f.path.suffix.lower(), "")
        lines.append(f"## {f.path.as_posix()}")
        lines.append("")
        lines.append(f"```{lang}")
        lines.append(f.text.rstrip("\n"))
        lines.append("```")
        lines.append("")

    if result.skipped:
        lines.append("## Skipped (over budget or unreadable)")
        lines.append("")
        for p in result.skipped:
            lines.append(f"- {p.as_posix()}")
        lines.append("")

    return "\n".join(lines)


def to_json(result: BudgetResult, root_label: str) -> str:
    payload = {
        "root": root_label,
        "total_tokens": result.total_tokens,
        "files": [
            {
                "path": f.path.as_posix(),
                "tokens": f.tokens,
                "score": round(f.score, 3),
                "content": f.text,
            }
            for f in result.included
        ],
        "skipped": [p.as_posix() for p in result.skipped],
    }
    return json.dumps(payload, indent=2)
