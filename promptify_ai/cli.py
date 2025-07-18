import argparse
import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import pyperclip


def _build_tree_lines(directory: Path, prefix: str = "") -> List[str]:
    """Recreate the output of the Unix ``tree`` command."""
    entries = sorted(
        [
            e
            for e in directory.iterdir()
            if not (e.is_dir() and (e.name.startswith(".") or e.name.startswith("__")))
        ]
    )
    lines: List[str] = []
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if idx == len(entries) - 1 else "│   "
            lines.extend(_build_tree_lines(entry, prefix + extension))
    return lines


@dataclass
class FileCollector:
    """Collect files from a directory matching given patterns."""

    source_dir: Path
    patterns: List[str]
    exclude_pattern: Optional[str] = None

    def collect(self) -> List[Path]:
        files: List[Path] = []
        for root, dirs, filenames in os.walk(self.source_dir):
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and not d.startswith("__")
                and not (
                    self.exclude_pattern
                    and fnmatch.fnmatch(d, self.exclude_pattern)
                )
            ]
            for filename in filenames:
                if any(fnmatch.fnmatch(filename, pat) for pat in self.patterns):
                    if self.exclude_pattern and fnmatch.fnmatch(
                        filename, self.exclude_pattern
                    ):
                        continue
                    files.append(Path(root) / filename)
        return sorted(files)


class PromptWriter:
    """Write gathered files to a single output file or return the prompt text."""

    FILE_START = "# === FILE START: {file} ===\n"
    FILE_END = "# === FILE END ===\n"
    TREE_START = "# === PROJECT TREE: {dir} ===\n"
    TREE_END = "# === END PROJECT TREE ===\n"
    INSTRUCTION_HEADER = "USER_REQUEST\n"
    TREE_HEADER = "TREE\n"
    CODE_HEADER = "CODE\n"

    def __init__(self, output_file: Optional[Path]) -> None:
        self.output_file = output_file

    def _write_instruction(self, out, instruction: str) -> None:
        out.write(self.INSTRUCTION_HEADER)
        out.write(instruction.strip() + "\n\n")

    def _write_tree(self, out, tree_dir: Path) -> None:
        out.write(self.TREE_HEADER)
        out.write(self.TREE_START.format(dir=tree_dir))
        for line in _build_tree_lines(tree_dir):
            out.write(line + "\n")
        out.write(self.TREE_END + "\n\n")

    def _write_all(self, out, files: Iterable[Path], tree_dir: Path, instruction: Optional[str]) -> None:
        if instruction:
            self._write_instruction(out, instruction)
        self._write_tree(out, tree_dir)
        out.write(self.CODE_HEADER)
        for file in files:
            out.write(self.FILE_START.format(file=file))
            out.write(file.read_text(encoding="utf-8"))
            out.write("\n" + self.FILE_END + "\n\n")

    def write(self, files: Iterable[Path], tree_dir: Path, instruction: Optional[str] = None) -> str:
        if self.output_file:
            with self.output_file.open("w", encoding="utf-8") as out:
                self._write_all(out, files, tree_dir, instruction)
            return self.output_file.read_text(encoding="utf-8")
        else:
            from io import StringIO
            buf = StringIO()
            self._write_all(buf, files, tree_dir, instruction)
            return buf.getvalue()


class ClipboardManager:
    """Utility class to copy content to the clipboard."""

    def copy(self, text: str, file: Optional[Path] = None) -> None:
        try:
            pyperclip.copy(text)
            if file:
                print(f"Output written to '{file}' and copied to clipboard.")
            else:
                print("Output copied to clipboard.")
        except pyperclip.PyperclipException:
            if file:
                print(
                    f"Output written to '{file}'. (pyperclip could not access the clipboard)"
                )
            else:
                print(
                    "Output generated. (pyperclip could not access the clipboard)"
                )


class Promptify:
    """Main application class orchestrating the prompt generation."""

    def __init__(
        self,
        source: Path,
        output: Optional[Path],
        patterns: List[str],
        exclude: Optional[str] = None,
        tree_dir: Optional[Path] = None,
        instruction: Optional[str] = None,
    ) -> None:
        self.collector = FileCollector(source, patterns, exclude)
        self.writer = PromptWriter(output)
        self.clipboard = ClipboardManager()
        self.tree_dir = tree_dir or source.parent
        self.instruction = instruction

    def run(self) -> None:
        files = self.collector.collect()
        text = self.writer.write(files, self.tree_dir, self.instruction)
        self.clipboard.copy(text, self.writer.output_file)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Gather files into a single prompt for LLM consumption",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-s", "--source", default="src", help="Source directory")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file (if omitted, only copy to clipboard)",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        nargs='+',
        default=["*.py"],
        help="File name pattern(s), e.g. '*.py' '*.j2'",
    )
    parser.add_argument("-e", "--exclude", default="", help="Pattern to exclude (files or directories)")
    parser.add_argument(
        "-t",
        "--tree",
        default=None,
        help="Directory to generate the tree from (defaults to parent of source)",
    )
    parser.add_argument(
        "-i",
        "--instruction",
        default=None,
        help="Instruction to prepend to the final prompt",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    promptify = Promptify(
        Path(args.source),
        Path(args.output) if args.output else None,
        args.pattern,
        args.exclude or None,
        Path(args.tree) if args.tree else None,
        args.instruction,
    )
    promptify.run()


if __name__ == "__main__":
    main()
