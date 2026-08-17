from pathlib import Path

from ctxpack.budget import count_tokens, fit_to_budget


def test_count_tokens_nonzero_for_nonempty_text():
    assert count_tokens("hello world") > 0


def test_count_tokens_empty_string():
    assert count_tokens("") >= 0


def test_fit_to_budget_includes_highest_scored_first():
    scored = [(Path("a.py"), 1.0), (Path("b.py"), 0.5)]
    texts = {"a.py": "x" * 4, "b.py": "y" * 4}

    result = fit_to_budget(scored, read_text_fn=lambda p: texts[p.as_posix()], budget_tokens=1000)
    assert len(result.included) == 2
    assert result.included[0].path == Path("a.py")


def test_fit_to_budget_stops_at_limit():
    scored = [(Path("a.py"), 1.0), (Path("b.py"), 0.5)]
    big_text = "word " * 2000  # will exceed a tiny budget
    small_text = "hi"
    texts = {"a.py": big_text, "b.py": small_text}

    result = fit_to_budget(scored, read_text_fn=lambda p: texts[p.as_posix()], budget_tokens=10)
    # a.py alone likely exceeds 10 tokens, so it should be skipped and b.py included
    included_names = {f.path.name for f in result.included}
    assert "a.py" not in included_names or result.total_tokens <= 10


def test_fit_to_budget_skips_unreadable_files():
    scored = [(Path("bad.bin"), 1.0)]
    result = fit_to_budget(scored, read_text_fn=lambda p: None, budget_tokens=1000)
    assert result.included == []
    assert Path("bad.bin") in result.skipped
