from pathlib import Path

from ctxpack.ranker import rank_files


def test_readme_and_pyproject_rank_highly(tmp_path):
    (tmp_path / "README.md").write_text("# hi\n")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "main.py").write_text("print(1)\n")
    (tmp_path / "data.lock").write_text("{}\n")

    paths = [Path("README.md"), Path("pyproject.toml"), Path("main.py"), Path("data.lock")]
    ranked = rank_files(tmp_path, paths)
    ranked_names = [p.name for p, _ in ranked]

    # Priority files should outrank the lock file.
    assert ranked_names.index("data.lock") == len(ranked_names) - 1


def test_test_directory_files_are_deprioritized(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_thing.py").write_text("def test_x(): pass\n")
    (tmp_path / "src_thing.py").write_text("def real_logic(): pass\n")

    paths = [Path("tests/test_thing.py"), Path("src_thing.py")]
    ranked = rank_files(tmp_path, paths)

    scores = dict(ranked)
    assert scores[Path("src_thing.py")] >= scores[Path("tests/test_thing.py")]


def test_rank_files_returns_all_input_paths(tmp_path):
    (tmp_path / "a.py").write_text("a\n")
    (tmp_path / "b.txt").write_text("b\n")
    paths = [Path("a.py"), Path("b.txt")]
    ranked = rank_files(tmp_path, paths)
    assert {p for p, _ in ranked} == set(paths)
