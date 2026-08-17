# Contributing to ctxpack

Thanks for considering a contribution. This is a small, focused CLI tool, so the bar for contributing is intentionally low.

## Getting set up

```bash
git clone https://github.com/DoshiTirth/ctxpack.git
cd ctxpack
pip install -e ".[dev]"
```

## Running checks locally before opening a PR

```bash
pytest                    # run the test suite
ruff check src tests      # lint
```

Both run in CI on every PR, so it saves a round-trip to check locally first.

## Making a change

1. Fork the repo and create a branch off `main`.
2. Make your change, with tests for new behavior where it makes sense.
3. Make sure `pytest` and `ruff check` both pass.
4. Open a PR with a short description of what changed and why.

## Reporting bugs / requesting features

Open an issue using the relevant template. For bugs, a minimal repro (a small directory structure + the command you ran) makes it much faster to track down.

## Code style

- Keep functions small and single-purpose — the existing modules (`walker`, `ranker`, `budget`, `secrets`) each do one thing.
- Prefer explicit dataclasses over dicts for structured return values (see `budget.py` for the pattern).
- New CLI flags should have a sensible default and be documented in the README.
