import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from promptify_ai.cli import FileCollector, PromptWriter, parse_args, Promptify


class TestFileCollector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        base = Path(self.temp_dir.name)
        (base / "a.py").write_text("print('a')")
        (base / "b.txt").write_text("text")
        sub = base / "sub"
        sub.mkdir()
        (sub / "c.py").write_text("print('c')")
        (sub / "ignore.py").write_text("print('ignore')")
        ignored_dir = base / "ignored"
        ignored_dir.mkdir()
        (ignored_dir / "d.py").write_text("print('d')")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collect_with_exclude(self):
        base = Path(self.temp_dir.name)
        collector = FileCollector(base, ["*.py"], "ignore*")
        files = collector.collect()
        relative = [f.relative_to(base).as_posix() for f in files]
        self.assertEqual(
            relative,
            ["a.py", "sub/c.py"],
        )

    def test_collect_multiple_patterns(self):
        base = Path(self.temp_dir.name)
        collector = FileCollector(base, ["*.py", "*.txt"])
        files = collector.collect()
        relative = [f.relative_to(base).as_posix() for f in files]
        self.assertEqual(
            relative,
            ["a.py", "b.txt", "ignored/d.py", "sub/c.py", "sub/ignore.py"],
        )


class TestPromptWriter(unittest.TestCase):
    def test_write_headers_multiple_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            file1 = base / "file1.txt"
            file2 = base / "file2.txt"
            file1.write_text("hello")
            file2.write_text("world")
            out = base / "out.llm"
            writer = PromptWriter(out)
            writer.write([file1, file2], base)
            content = out.read_text()
            self.assertEqual(content.count("# === FILE START:"), 2)
            self.assertIn(f"# === FILE START: {file1}", content)
            self.assertIn("hello", content)
            self.assertIn(f"# === FILE START: {file2}", content)
            self.assertIn("world", content)


class TestParseArgs(unittest.TestCase):
    def test_custom_args(self):
        args = parse_args([
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
        ])
        self.assertEqual(args.source, "src")
        self.assertEqual(args.output, "out.txt")
        self.assertEqual(args.pattern, ["*.txt", "*.py"])
        self.assertEqual(args.exclude, "venv")
        self.assertEqual(args.instruction, "do something")

    def test_defaults(self):
        args = parse_args([])
        self.assertEqual(args.source, "src")
        self.assertEqual(args.output, "prompt.llm")
        self.assertEqual(args.pattern, ["*.py"])
        self.assertEqual(args.exclude, "")
        self.assertIsNone(args.instruction)


class TestPromptifyIntegration(unittest.TestCase):
    def test_run_writes_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            src = base / "src"
            src.mkdir()
            file1 = src / "x.py"
            file1.write_text("print('x')")
            out = base / "out.llm"
            prompt = Promptify(src, out, ["*.py"], instruction="do it")
            with patch.object(prompt.clipboard, "copy") as mock_copy:
                prompt.run()
                mock_copy.assert_called_once_with(out)
            self.assertTrue(out.exists())
            text = out.read_text()
            self.assertIn("x.py", text)
            self.assertIn("do it", text.splitlines()[1])

    def test_main_invocation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            src = base / "app"
            src.mkdir()
            (src / "y.py").write_text("print('y')")
            out = base / "context.llm"
            with patch("promptify_ai.cli.Promptify") as MockPromptify:
                instance = MockPromptify.return_value
                from promptify_ai.cli import main

                main(["-s", str(src), "-o", str(out), "-p", "*.py", "-i", "inst"])

                MockPromptify.assert_called_once_with(
                    src, out, ["*.py"], None, None, "inst"
                )
                instance.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
