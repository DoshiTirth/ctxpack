from ctxpack.secrets import scan_and_redact


def test_redacts_github_pat():
    text = 'token = "github_pat_11ABCDEF0123456789012345678901234567890123456789012345"\n'
    redacted, findings = scan_and_redact(text)
    assert "github_pat_11ABCDEF" not in redacted
    assert any(f.kind == "github_fine_grained" for f in findings)


def test_redacts_aws_access_key():
    text = "key = AKIAABCDEFGHIJKLMNOP\n"
    redacted, findings = scan_and_redact(text)
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert any(f.kind == "aws_access_key" for f in findings)


def test_redacts_private_key_block():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJ...\n-----END RSA PRIVATE KEY-----\n"
    redacted, findings = scan_and_redact(text)
    assert "BEGIN RSA PRIVATE KEY" not in redacted
    assert any(f.kind == "private_key_block" for f in findings)


def test_leaves_normal_code_untouched():
    text = "def add(a, b):\n    return a + b\n"
    redacted, findings = scan_and_redact(text)
    assert redacted == text
    assert findings == []


def test_reports_line_numbers():
    text = "line1\nline2\napi_key = 'AKIAABCDEFGHIJKLMNOP'\n"
    _, findings = scan_and_redact(text)
    assert any(f.line_number == 3 for f in findings)
