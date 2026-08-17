from pathlib import Path

from ctxpack.walker import WalkOptions, walk_repo


def _make_tree(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("// junk\n")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
    (tmp_path / "README.md").write_text("# hi\n")
    (tmp_path / ".gitignore").write_text("ignored_dir/\n")
    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "secret.txt").write_text("nope\n")
    return tmp_path


def test_walk_respects_default_ignores(tmp_path):
    root = _make_tree(tmp_path)
    results = walk_repo(root)
    result_strs = {p.as_posix() for p in results}

    assert "src/main.py" in result_strs
    assert "README.md" in result_strs
    assert not any("node_modules" in r for r in result_strs)


def test_walk_respects_gitignore(tmp_path):
    root = _make_tree(tmp_path)
    results = walk_repo(root)
    result_strs = {p.as_posix() for p in results}
    assert "ignored_dir/secret.txt" not in result_strs


def test_walk_skips_binary_extensions(tmp_path):
    root = _make_tree(tmp_path)
    results = walk_repo(root)
    result_strs = {p.as_posix() for p in results}
    assert "image.png" not in result_strs


def test_walk_can_disable_gitignore(tmp_path):
    root = _make_tree(tmp_path)
    options = WalkOptions(respect_gitignore=False)
    results = walk_repo(root, options)
    result_strs = {p.as_posix() for p in results}
    assert "ignored_dir/secret.txt" in result_strs


def test_walk_include_glob_restricts_results(tmp_path):
    root = _make_tree(tmp_path)
    options = WalkOptions(include_globs=["*.py"])
    results = walk_repo(root, options)
    result_strs = {p.as_posix() for p in results}
    assert result_strs == {"src/main.py"}


def test_walk_exclude_glob(tmp_path):
    root = _make_tree(tmp_path)
    options = WalkOptions(exclude_globs=["README.md"])
    results = walk_repo(root, options)
    result_strs = {p.as_posix() for p in results}
    assert "README.md" not in result_strs
