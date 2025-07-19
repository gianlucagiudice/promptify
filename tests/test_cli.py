from pathlib import Path
from unittest.mock import patch

import pytest

from promptify_ai.cli import FileCollector, PromptWriter, Promptify, parse_args


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    base = tmp_path
    (base / "a.py").write_text("print('a')")
    (base / "b.txt").write_text("text")
    sub = base / "sub"
    sub.mkdir()
    (sub / "c.py").write_text("print('c')")
    (sub / "ignore.py").write_text("print('ignore')")
    ignored_dir = base / "ignored"
    ignored_dir.mkdir()
    (ignored_dir / "d.py").write_text("print('d')")
    return base


def test_filecollector_with_exclude(sample_dir: Path):
    collector = FileCollector(sample_dir, ["*.py"], "ignore*")
    files = collector.collect()
    relative = [f.relative_to(sample_dir).as_posix() for f in files]
    assert relative == ["a.py", "sub/c.py"]


def test_filecollector_multiple_patterns(sample_dir: Path):
    collector = FileCollector(sample_dir, ["*.py", "*.txt"])
    files = collector.collect()
    relative = [f.relative_to(sample_dir).as_posix() for f in files]
    assert relative == [
        "a.py",
        "b.txt",
        "ignored/d.py",
        "sub/c.py",
        "sub/ignore.py",
    ]


def test_filecollector_skips_hidden_and_dunder_dirs(tmp_path: Path):
    base = tmp_path
    hidden = base / ".hidden"
    hidden.mkdir()
    (hidden / "x.py").write_text("print('x')")
    dunder = base / "__cache__"
    dunder.mkdir()
    (dunder / "y.py").write_text("print('y')")
    visible = base / "vis"
    visible.mkdir()
    (visible / "z.py").write_text("print('z')")

    collector = FileCollector(base, ["*.py"])
    files = collector.collect()
    relative = [f.relative_to(base).as_posix() for f in files]
    assert relative == ["vis/z.py"]


def test_promptwriter_headers(tmp_path: Path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("hello")
    file2.write_text("world")
    out = tmp_path / "out.llm"
    writer = PromptWriter(out)
    writer.write([file1, file2], tmp_path)
    content = out.read_text()
    assert content.count("# === BEGIN FILE:") == 2
    assert f"# === BEGIN FILE: {file1}" in content
    assert "hello" in content
    assert f"# === BEGIN FILE: {file2}" in content
    assert "world" in content


def test_parse_args_custom():
    args = parse_args(
        [
            "-s",
            "src",
            "-o",
            "out.txt",
            "-p",
            "*.txt",
            "*.py",
            "-e",
            "venv",
            "-i",
            "do something",
        ]
    )
    assert args.source == "src"
    assert args.output == "out.txt"
    assert args.pattern == ["*.txt", "*.py"]
    assert args.exclude == "venv"
    assert args.instruction == "do something"


def test_parse_args_defaults():
    args = parse_args([])
    assert args.source == "src"
    assert args.output is None
    assert args.pattern == ["*.py"]
    assert args.exclude == ""
    assert args.instruction is None


def test_promptify_run(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "x.py").write_text("print('x')")
    out = tmp_path / "out.llm"
    prompt = Promptify(src, out, ["*.py"], instruction="do it")
    with patch.object(prompt.clipboard, "copy") as mock_copy:
        prompt.run()
        assert mock_copy.call_count == 1
        args_called = mock_copy.call_args[0]
        assert args_called[1] == out
    assert out.exists()
    text = out.read_text()
    assert "x.py" in text
    assert "do it" in text.splitlines()[1]


def test_main_invocation(tmp_path: Path):
    src = tmp_path / "app"
    src.mkdir()
    (src / "y.py").write_text("print('y')")
    out = tmp_path / "context.llm"
    with patch("promptify_ai.cli.Promptify") as MockPromptify:
        instance = MockPromptify.return_value
        from promptify_ai.cli import main

        main(["-s", str(src), "-o", str(out), "-p", "*.py", "-i", "inst"])

        MockPromptify.assert_called_once_with(src, out, ["*.py"], None, None, "inst")
        instance.run.assert_called_once()
