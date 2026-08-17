"""Detect and redact likely secrets before they end up in a shared context bundle.

This is a best-effort heuristic scanner, not a substitute for a dedicated
secret-scanning tool. It aims to catch common, high-confidence patterns
(API keys, private keys, connection strings with embedded credentials) so
they don't accidentally leak into a bundle you paste into a chat or ship
in a public repo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "aws_secret_key",
        re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?"),
    ),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe_key", re.compile(r"\b(sk|pk|rk)_(live|test)_[A-Za-z0-9]{16,}\b")),
    (
        "generic_api_key",
        re.compile(
            r"(?i)(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*"
            r"['\"][A-Za-z0-9_\-]{16,}['\"]"
        ),
    ),
    ("private_key_block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("basic_auth_url", re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s:'\"/]+:[^\s@'\"/]+@")),
]

REDACTED_MARKER = "[REDACTED:{kind}]"


@dataclass
class SecretFinding:
    kind: str
    line_number: int


def scan_and_redact(text: str) -> tuple[str, list[SecretFinding]]:
    """Return (redacted_text, findings). Findings are reported, not just silently dropped."""
    findings: list[SecretFinding] = []
    lines = text.splitlines(keepends=True)

    for idx, line in enumerate(lines, start=1):
        redacted_line = line
        for kind, pattern in _PATTERNS:
            if pattern.search(redacted_line):
                findings.append(SecretFinding(kind=kind, line_number=idx))
                redacted_line = pattern.sub(REDACTED_MARKER.format(kind=kind), redacted_line)
        lines[idx - 1] = redacted_line

    return "".join(lines), findings
