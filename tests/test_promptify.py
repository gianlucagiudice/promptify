from pathlib import Path
import pyperclip
import pytest

from promptify_ai.cli import _build_tree_lines, Promptify, parse_args


def test_build_tree_lines(tmp_path):
    app = tmp_path / "app"
    src = app / "src"
    sub = src / "sub"
    sub.mkdir(parents=True)
    (src / "file1.txt").write_text("a")
    (sub / "file2.txt").write_text("b")

    lines = _build_tree_lines(app)
    assert lines == [
        "└── src",
        "    ├── file1.txt",
        "    └── sub",
        "        └── file2.txt",
    ]


def test_build_tree_lines_skip_hidden_and_dunder(tmp_path):
    root = tmp_path
    hidden = root / ".hidden"
    hidden.mkdir()
    (hidden / "a.txt").write_text("ignore")
    dunder = root / "__pycache__"
    dunder.mkdir()
    (dunder / "b.txt").write_text("ignore")
    src = root / "src"
    src.mkdir()

    lines = _build_tree_lines(root)
    combined = "\n".join(lines)
    assert ".hidden" not in combined
    assert "__pycache__" not in combined


def test_promptify_default_tree(tmp_path, monkeypatch):
    app = tmp_path / "app"
    src = app / "src"
    sub = src / "sub"
    sub.mkdir(parents=True)
    f1 = src / "f1.txt"
    f2 = sub / "f2.txt"
    f1.write_text("hello")
    f2.write_text("bye")

    out = tmp_path / "out.llm"

    monkeypatch.setattr(pyperclip, "copy", lambda text: None)

    prompt = Promptify(source=src, output=out, patterns=["*.txt"], exclude=None)
    prompt.run()

    data = out.read_text()
    assert "# === BEGIN PROJECT TREE:" in data
    assert "└── src" in data
    assert "f1.txt" in data and "f2.txt" in data
    assert data.count("# === BEGIN FILE:") == 2
    assert prompt.tree_dir == app


def test_promptify_custom_tree(tmp_path, monkeypatch):
    app = tmp_path / "app"
    src = app / "src"
    sub = src / "sub"
    sub.mkdir(parents=True)
    (src / "f.txt").write_text("hi")

    custom_tree = tmp_path
    out = tmp_path / "out.llm"

    monkeypatch.setattr(pyperclip, "copy", lambda text: None)

    args = parse_args(["-s", str(src), "-o", str(out), "-t", str(custom_tree)])
    prompt = Promptify(
        Path(args.source), Path(args.output), args.pattern, args.exclude or None, Path(args.tree)
    )
    prompt.run()

    data = out.read_text()
    assert f"# === BEGIN PROJECT TREE: {custom_tree}" in data
    assert prompt.tree_dir == custom_tree


def test_promptify_with_instruction(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "file.txt"
    f.write_text("hello")

    out = tmp_path / "out.llm"

    monkeypatch.setattr(pyperclip, "copy", lambda text: None)

    prompt = Promptify(source=src, output=out, patterns=["*.txt"], instruction="say hi")
    prompt.run()

    lines = out.read_text().splitlines()
    assert lines[0] == "USER_REQUEST"
    assert lines[1] == "say hi"
    assert "FILES" in lines


def test_promptify_no_output(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "file.txt").write_text("hi")

    monkeypatch.setattr(pyperclip, "copy", lambda text: None)

    prompt = Promptify(source=src, output=None, patterns=["*.txt"])
    prompt.run()

    # ensure no .llm file was created in tmp_path
    assert not any(p.suffix == ".llm" for p in tmp_path.iterdir())
