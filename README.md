# ctxpack

Pack a codebase into an LLM-ready context bundle — gitignore-aware, token-budgeted, and scrubbed of likely secrets before it ever leaves your machine.

## Why

When you paste a codebase into an LLM chat or feed it to an API, you're usually doing three things by hand: figuring out which files actually matter, trimming everything down to fit a token limit, and double-checking you didn't just paste an API key into a prompt. `ctxpack` does all three in one command.

```bash
ctxpack pack . --budget 50000
```

## Install

```bash
pip install ctxpack
```

## Usage

```bash
# Pack the current directory into Markdown, printed to stdout
ctxpack pack .

# Set a token budget (defaults to 50,000)
ctxpack pack . --budget 20000

# Write to a file instead of stdout
ctxpack pack . --out context.md

# JSON output (useful for feeding into another tool/API call)
ctxpack pack . --format json --out context.json

# Restrict to specific files
ctxpack pack . --include "src/**/*.py" --include "*.md"

# Exclude noisy paths beyond what .gitignore already covers
ctxpack pack . --exclude "**/migrations/**"

# Ignore .gitignore entirely
ctxpack pack . --no-gitignore
```

### How files are chosen

`ctxpack` walks the repo (skipping anything `.gitignore`'d, plus common noise like `node_modules/`, `__pycache__/`, lockfiles, and binaries), scores every remaining file by relevance — recent git activity, file type, whether it's something like a `README` or `pyproject.toml` — and then greedily fills your token budget with the highest-scoring files first. Anything that doesn't fit is listed as skipped, not silently dropped.

### Secret scrubbing

Before any file's content makes it into the bundle, `ctxpack` runs a pattern-based scan for common secret shapes (AWS keys, GitHub tokens, Slack tokens, Stripe keys, private key blocks, JWTs, credentials embedded in URLs, and generic `key = "..."`-style assignments) and redacts matches in place, replacing them with a `[REDACTED:kind]` marker. This is a heuristic safety net, not a guarantee — always review a bundle before sharing it externally.

### Config file

Drop a `.ctxpack.yml` in your repo root to set repeatable defaults:

```yaml
budget: 30000
output_format: markdown
respect_gitignore: true
include:
  - "src/**"
exclude:
  - "**/*.generated.*"
```

CLI flags override the config file when both are given.

## Development

```bash
git clone https://github.com/DoshiTirth/ctxpack.git
cd ctxpack
pip install -e ".[dev]"
pytest
ruff check src tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more.

## License

Apache 2.0 — see [LICENSE](LICENSE).
