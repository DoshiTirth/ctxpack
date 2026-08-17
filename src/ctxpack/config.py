"""Load repeatable settings from a .ctxpack.yml file, if present."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    budget: int = 50_000
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    output_format: str = "markdown"
    respect_gitignore: bool = True

    @classmethod
    def load(cls, root: str | Path) -> "Config":
        path = Path(root) / ".ctxpack.yml"
        if not path.exists():
            return cls()

        data = yaml.safe_load(path.read_text()) or {}
        return cls(
            budget=int(data.get("budget", cls.budget)),
            include=list(data.get("include", [])),
            exclude=list(data.get("exclude", [])),
            output_format=str(data.get("output_format", cls.output_format)),
            respect_gitignore=bool(data.get("respect_gitignore", cls.respect_gitignore)),
        )
