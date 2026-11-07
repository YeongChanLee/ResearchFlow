"""Explicit distribution inventory shared by packaging and publishing tools."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"README.md", "README.ko.md", "LICENSE", "CHANGELOG.md", "CITATION.cff", "CONTRIBUTING.md", "SECURITY.md", "AGENTS.md", "VERSION", ".gitignore", ".gitattributes"}
ROOT_DIRS = {"skills", "docs", "tools", "tests", "evals", "examples", ".github"}
SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".cff", ".png"}
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".venv", "node_modules", ".git", "dist", "workspaces", "private"}


def distribution_files(root: Path = ROOT) -> list[Path]:
    files = []
    for name in sorted(ROOT_FILES | ROOT_DIRS):
        path = root / name
        if path.is_symlink():
            raise ValueError(f"Distribution path is a symlink: {name}")
        if not path.exists():
            raise ValueError(f"Missing distribution path: {name}")
        entries = [path] if path.is_file() else sorted(path.rglob("*"))
        for entry in entries:
            relative = entry.relative_to(root)
            if any(part in SKIP_PARTS for part in relative.parts):
                continue
            if entry.is_symlink():
                raise ValueError(f"Symlink in distribution: {relative}")
            if entry.is_file():
                if entry.name.startswith(".env") or entry.suffix in {".pem", ".key", ".p12"}:
                    raise ValueError(f"Potential private material in distribution: {relative}")
                if relative.as_posix() in ROOT_FILES or entry.suffix in SUFFIXES:
                    files.append(entry)
                elif entry.suffix not in {".pyc", ".pyo"} and entry.name not in {".DS_Store", "Thumbs.db"}:
                    raise ValueError(f"Unexpected distribution file: {relative}")
    return sorted(files)
