import argparse
import fnmatch
import os
from pathlib import Path
import subprocess
import shutil


def gather_files(source_dir: Path, patterns, exclude_pattern=None):
    files = []
    for root, dirs, filenames in os.walk(source_dir):
        if exclude_pattern:
            dirs[:] = [d for d in dirs if not fnmatch.fnmatch(d, exclude_pattern)]
        for filename in filenames:
            if any(fnmatch.fnmatch(filename, pat) for pat in patterns):
                if exclude_pattern and fnmatch.fnmatch(filename, exclude_pattern):
                    continue
                files.append(Path(root) / filename)
    return sorted(files)


def write_output(files, output_file: Path):
    with output_file.open("w", encoding="utf-8") as out:
        for file in files:
            out.write("\n")
            out.write("# ===============================================================\n")
            out.write(f"# FILE: {file}\n")
            out.write("# ===============================================================\n")
            out.write(file.read_text(encoding="utf-8"))


def copy_to_clipboard(output_file: Path):
    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=output_file.read_bytes())
        print(f"Output written to '{output_file}' and copied to clipboard.")
    else:
        print(f"Output written to '{output_file}'. (pbcopy not available)")


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
    patterns = args.pattern
    files = gather_files(Path(args.source), patterns, args.exclude or None)
    output_file = Path(args.output)
    write_output(files, output_file)
    copy_to_clipboard(output_file)


if __name__ == "__main__":
    main()
