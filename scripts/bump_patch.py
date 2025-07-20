#!/usr/bin/env python
"""
Bump the patch component of the version string in pyproject.toml
and __init__.py.

Example:
    1.4.2  ->  1.4.3
"""

import pathlib
import re

import toml

# --- Paths --------------------------------------------------------------

PYPROJECT = pathlib.Path("pyproject.toml")
INIT_FILE = pathlib.Path("promptify_ai/__init__.py")  # adjust if your package path differs

# --- Helpers ------------------------------------------------------------

def read_version() -> str:
    """Return the current version string X.Y.Z from pyproject.toml."""
    data = toml.load(PYPROJECT)
    return data["project"]["version"]


def write_version(new_version: str) -> None:
    """Persist *new_version* to pyproject.toml and package __init__.py."""
    # 1) pyproject.toml
    data = toml.load(PYPROJECT)
    data["project"]["version"] = new_version
    PYPROJECT.write_text(toml.dumps(data))

    # 2) promptify_ai/__init__.py
    content = INIT_FILE.read_text()
    content = re.sub(r'__version__\s*=\s*"[0-9.]+"',
                     f'__version__ = "{new_version}"',
                     content)
    INIT_FILE.write_text(content)


def bump_patch(current: str) -> str:
    """Return new version string with patch += 1."""
    major, minor, patch = map(int, current.split("."))
    patch += 1
    return f"{major}.{minor}.{patch}"


# --- Main ---------------------------------------------------------------

def main() -> None:
    current_version = read_version()
    new_version = bump_patch(current_version)
    write_version(new_version)
    print(new_version)          # output is captured by the GitHub Action


if __name__ == "__main__":
    main()