#!/usr/bin/env python3
"""Install the local ResearchFlow skill without network access or overwriting files."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "researchflow"


def destination_for(target: str, project: Path | None = None) -> Path:
    if target not in {"claude", "codex"}:
        raise ValueError("Target must be claude or codex")
    base = project.expanduser().absolute() if project else Path.home()
    return base / (".claude" if target == "claude" else ".agents") / "skills" / "researchflow"


def install(destination: Path, source: Path = SOURCE) -> Path:
    destination = destination.expanduser().absolute()
    if destination.name != "researchflow":
        raise ValueError("The final destination directory must be named researchflow")
    if not (source / "SKILL.md").is_file() or source.is_symlink():
        raise ValueError("Canonical source skill is missing or is a symlink")
    if any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("Refusing to install a package containing symlinks")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Installation already exists; back it up and remove it deliberately before updating")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".researchflow-install-", dir=destination.parent))
    try:
        staged_skill = staging / "researchflow"
        shutil.copytree(source, staged_skill, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"))
        if destination.exists() or destination.is_symlink():
            raise ValueError("Destination appeared during installation; refusing overwrite")
        staged_skill.rename(destination)
    finally:
        shutil.rmtree(staging)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", choices=("claude", "codex"))
    group.add_argument("--destination", type=Path)
    parser.add_argument("--project", type=Path, help="Project-scoped installation instead of personal")
    args = parser.parse_args(argv)
    if args.destination is not None and args.project is not None:
        parser.error("--project requires --target, not --destination")
    try:
        destination = args.destination if args.destination is not None else destination_for(args.target, args.project)
        installed = install(destination)
        print(f"Installed local skill files: {installed}")
        print("Host discovery/invocation must be verified separately; no connectors or accounts were changed.")
        return 0
    except (ValueError, OSError) as exc:
        print(f"Installation stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
