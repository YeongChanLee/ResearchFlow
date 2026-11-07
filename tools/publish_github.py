#!/usr/bin/env python3
"""Publish a NEW personal ResearchFlow repository only with explicit --execute.

Dry-run default makes no network calls and performs no writes. Never paste credentials
into this program; use an existing GitHub CLI browser/device-flow login.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import ROOT, distribution_files


def validate_owner(owner: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", owner):
        raise ValueError("Invalid personal GitHub account name")
    return owner


def run(args: list[str], *, root: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, GH_HOST="github.com", GIT_TERMINAL_PROMPT="0", GH_PROMPT_DISABLED="1")
    result = subprocess.run(args, cwd=root, env=env, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise ValueError(f"Command failed ({args[0]} {args[1]}): {result.stderr.strip() or result.stdout.strip()}")
    return result


def plan(owner: str, root: Path = ROOT) -> dict:
    owner = validate_owner(owner)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    return {"mode": "dry_run", "repository": f"{owner}/ResearchFlow", "visibility": "public", "license": "MIT", "release": f"v{version}", "prerelease": True, "steps": ["Verify local tools and the authenticated GitHub account", "Run tests, lint and deterministic packaging", "Verify the remote repository does not already exist", "Create fresh local git metadata and stage only distribution files", "Create the public repository and push main without force", "Verify remote commit and upload prerelease packages"], "notice": "No commands executed, files changed, or network calls made. Review license and use --execute to publish."}


def execute(owner: str, root: Path = ROOT) -> dict:
    owner = validate_owner(owner)
    for program in ("git", "gh"):
        if not shutil.which(program):
            raise ValueError(f"Missing required publishing tool: {program}. Install it and authenticate gh through its normal browser/device flow.")
    if (root / ".git").exists():
        raise ValueError("Existing git metadata detected; use a fresh extracted source directory. No existing repository was modified.")
    identity = run(["gh", "api", "--hostname", "github.com", "user", "--jq", ".login"], root=root).stdout.strip()
    if identity.lower() != owner.lower():
        raise ValueError(f"Authenticated account {identity!r} does not match requested owner {owner!r}")
    # Validate before any remote write or local repository creation.
    for command in ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], [sys.executable, "tools/validate_package.py"], [sys.executable, "tools/build_release.py"]):
        result = run(command, root=root)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
    repository = f"{owner}/ResearchFlow"
    probe = run(["gh", "api", "--hostname", "github.com", f"repos/{repository}", "--silent"], root=root, check=False)
    if probe.returncode == 0:
        raise ValueError("Remote repository already exists; refusing to replace or push into it automatically")
    if "HTTP 404" not in probe.stderr:
        raise ValueError("Cannot establish repository absence; stopped without publishing: " + probe.stderr.strip())
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    files = distribution_files(root)
    relative = [p.relative_to(root).as_posix() for p in files]
    run(["git", "init", "--initial-branch=main"], root=root)
    # Explicit file inventory, not `git add .`; private workspaces stay out.
    run(["git", "add", "--", *relative], root=root)
    staged = set(run(["git", "diff", "--cached", "--name-only"], root=root).stdout.splitlines())
    if staged != set(relative):
        raise ValueError("Staged inventory differs from the reviewed distribution; stopped before publication")
    run(["git", "-c", "user.name=ResearchFlow", "-c", "user.email=researchflow@users.noreply.github.com", "-c", "commit.gpgSign=false", "-c", f"core.hooksPath={root / '.git/researchflow-no-hooks'}", "commit", "-m", f"Initial ResearchFlow skill v{version}"], root=root)
    commit = run(["git", "rev-parse", "HEAD"], root=root).stdout.strip()
    run(["gh", "repo", "create", repository, "--public", "--description", "Scientist-in-the-Loop Agile Research Specification", "--source", str(root), "--remote", "origin", "--push"], root=root)
    remote_commit = run(["gh", "api", "--hostname", "github.com", f"repos/{repository}/commits/main", "--jq", ".sha"], root=root).stdout.strip()
    if remote_commit != commit:
        raise ValueError("Repository was created but the remote commit could not be verified; no release uploaded")
    packages = [root / "dist" / f"researchflow-skill-{version}.zip", root / "dist" / f"ResearchFlow-source-{version}.zip", root / "dist/SHA256SUMS.txt"]
    release = run(["gh", "release", "create", f"v{version}", *map(str, packages), "--repo", repository, "--target", "main", "--prerelease", "--title", f"ResearchFlow v{version}", "--notes-file", "CHANGELOG.md"], root=root)
    return {"published": True, "repository": f"https://github.com/{repository}", "commit": commit, "release_output": release.stdout.strip(), "notice": "GitHub publication verified; host installation, marketplace listing and CI completion remain separate checks."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="YeongChanLee")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = execute(args.owner) if args.execute else plan(args.owner)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as exc:
        print(json.dumps({"published": False, "error": str(exc), "note": "If a remote repository was created before an error, inspect it before retrying; never force-push."}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
