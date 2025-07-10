import argparse
import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pyperclip


@dataclass
class FileCollector:
    """Collect files from a directory matching given patterns."""

    source_dir: Path
    patterns: List[str]
    exclude_pattern: Optional[str] = None

    def collect(self) -> List[Path]:
        files: List[Path] = []
        for root, dirs, filenames in os.walk(self.source_dir):
            if self.exclude_pattern:
                dirs[:] = [
                    d for d in dirs if not fnmatch.fnmatch(d, self.exclude_pattern)
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
    """Write gathered files to a single output file."""

    HEADER = "# ===============================================================\n"

    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file

    def write(self, files: Iterable[Path]) -> None:
        with self.output_file.open("w", encoding="utf-8") as out:
            for file in files:
                out.write("\n")
                out.write(self.HEADER)
                out.write(f"# FILE: {file}\n")
                out.write(self.HEADER)
                out.write(file.read_text(encoding="utf-8"))


class ClipboardManager:
    """Utility class to copy content to the clipboard."""

    def copy(self, file: Path) -> None:
        try:
            pyperclip.copy(file.read_text(encoding="utf-8"))
            print(f"Output written to '{file}' and copied to clipboard.")
        except pyperclip.PyperclipException:
            print(
                f"Output written to '{file}'. (pyperclip could not access the clipboard)"
            )


class Promptify:
    """Main application class orchestrating the prompt generation."""

    def __init__(
        self,
        source: Path,
        output: Path,
        patterns: List[str],
        exclude: Optional[str] = None,
    ) -> None:
        self.collector = FileCollector(source, patterns, exclude)
        self.writer = PromptWriter(output)
        self.clipboard = ClipboardManager()

    def run(self) -> None:
        files = self.collector.collect()
        self.writer.write(files)
        self.clipboard.copy(self.writer.output_file)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Gather files into a single prompt for LLM consumption",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-s", "--source", default="src", help="Source directory")
    parser.add_argument("-o", "--output", default="prompt.llm", help="Output file")
    parser.add_argument(
        "-p",
        "--pattern",
        nargs='+',
        default=["*.py"],
        help="File name pattern(s), e.g. '*.py' '*.j2'",
    )
    parser.add_argument("-e", "--exclude", default="", help="Pattern to exclude (files or directories)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    promptify = Promptify(
        Path(args.source), Path(args.output), args.pattern, args.exclude or None
    )
    promptify.run()


if __name__ == "__main__":
    main()
