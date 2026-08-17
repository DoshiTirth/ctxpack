"""Command-line interface for ctxpack."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .budget import fit_to_budget
from .config import Config
from .output import to_json, to_markdown
from .ranker import rank_files
from .secrets import scan_and_redact
from .walker import WalkOptions, walk_repo


def _read_text_and_scrub(root: Path, rel_path: Path, findings_log: list) -> str | None:
    abs_path = root / rel_path
    try:
        raw = abs_path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return None

    redacted, findings = scan_and_redact(raw)
    for f in findings:
        findings_log.append((rel_path, f.kind, f.line_number))
    return redacted


@click.group()
@click.version_option(version=__version__, prog_name="ctxpack")
def main() -> None:
    """ctxpack: pack a codebase into an LLM-ready context bundle."""


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--budget", "budget_tokens", type=int, default=None, help="Max tokens for the bundle.")
@click.option("--format", "output_format", type=click.Choice(["markdown", "json"]), default=None)
@click.option("--out", "out_path", type=click.Path(), default=None, help="Write output to a file instead of stdout.")
@click.option("--include", multiple=True, help="Glob(s) to restrict inclusion to.")
@click.option("--exclude", multiple=True, help="Glob(s) to exclude.")
@click.option("--no-gitignore", is_flag=True, help="Don't respect .gitignore.")
@click.option("--quiet", is_flag=True, help="Suppress the summary printed to stderr.")
def pack(
    directory: str,
    budget_tokens: int | None,
    output_format: str | None,
    out_path: str | None,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    no_gitignore: bool,
    quiet: bool,
) -> None:
    """Pack DIRECTORY into an LLM-ready context bundle."""
    root = Path(directory).resolve()
    config = Config.load(root)

    budget_tokens = budget_tokens if budget_tokens is not None else config.budget
    output_format = output_format if output_format is not None else config.output_format
    include_globs = list(include) or config.include
    exclude_globs = list(exclude) or config.exclude
    respect_gitignore = (not no_gitignore) and config.respect_gitignore

    walk_options = WalkOptions(
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        respect_gitignore=respect_gitignore,
    )
    paths = walk_repo(root, walk_options)
    if not paths:
        click.echo("No files matched — check your include/exclude patterns.", err=True)
        sys.exit(1)

    scored = rank_files(root, paths)

    findings_log: list = []
    result = fit_to_budget(
        scored,
        read_text_fn=lambda p: _read_text_and_scrub(root, p, findings_log),
        budget_tokens=budget_tokens,
    )

    rendered = to_markdown(result, root.name) if output_format == "markdown" else to_json(result, root.name)

    if out_path:
        Path(out_path).write_text(rendered, encoding="utf-8")
    else:
        click.echo(rendered)

    if not quiet:
        click.echo(
            f"\n[ctxpack] {len(result.included)} files included, "
            f"{len(result.skipped)} skipped, ~{result.total_tokens} tokens.",
            err=True,
        )
        if findings_log:
            click.echo(
                f"[ctxpack] Redacted {len(findings_log)} likely secret(s) before output "
                f"(see --format json for per-file detail is not yet supported; "
                f"kinds found: {sorted({k for _, k, _ in findings_log})}).",
                err=True,
            )


if __name__ == "__main__":
    main()
