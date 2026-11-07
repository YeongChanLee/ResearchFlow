#!/usr/bin/env python3
"""Repository-specific lint; not a general YAML or scientific-validity validator."""
from __future__ import annotations
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import ROOT, distribution_files

STAGES = ["Research Framing", "Literature Discovery & Workflow Reconstruction", "Data & Resource Co-design", "Methodology & Evaluation Design", "Specification Review & Baseline Approval"]


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    files = distribution_files(root)
    skill = root / "skills/researchflow"
    content = (skill / "SKILL.md").read_text(encoding="utf-8")
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        errors.append("SKILL.md YAML frontmatter missing")
    else:
        front = content.split("---\n", 2)[1]
        name = re.search(r"^name: (.+)$", front, re.M)
        description = re.search(r'^description: (".*")$', front, re.M)
        if not name or name.group(1) != skill.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name.group(1)) or len(name.group(1)) > 64:
            errors.append("Invalid skill name or directory mismatch")
        if not description:
            errors.append("Use this repository's single-line double-quoted description format")
        else:
            try:
                desc = json.loads(description.group(1))
                if not isinstance(desc, str) or not 1 <= len(desc) <= 1024:
                    errors.append("Description length outside Agent Skills limits")
            except json.JSONDecodeError:
                errors.append("Description quoting is invalid")
    if len(content.splitlines()) > 400:
        errors.append("SKILL.md too long for this project's progressive-disclosure target")
    for stage in STAGES:
        if stage not in content:
            errors.append(f"Stage missing from skill: {stage}")
    template = json.loads((skill / "assets/templates/project_state.json").read_text(encoding="utf-8"))
    if [s["name"] for s in template["stages"]] != STAGES:
        errors.append("Template stage names/order changed")
    spec = (skill / "assets/templates/research_spec.md").read_text(encoding="utf-8")
    if re.findall(r"^## [1-5]\. (.+)$", spec, re.M) != STAGES:
        errors.append("Specification template stage headings changed")
    version = (root / "VERSION").read_text().strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version) or f'version: "{version}"' not in content:
        errors.append("Package version mismatch")
    if (root / "LICENSE").read_bytes() != (skill / "LICENSE.txt").read_bytes():
        errors.append("Bundled license differs from repository license")
    patterns = [re.compile(r"ghp_[A-Za-z0-9]{30,}"), re.compile(r"github_pat_[A-Za-z0-9_]{50,}"), re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")]
    for path in files:
        if path.suffix == ".png":
            continue
        text = path.read_text(encoding="utf-8")
        if any(pattern.search(text) for pattern in patterns):
            errors.append(f"Potential secret in {path.relative_to(root)}")
        if path.suffix == ".py":
            try:
                ast.parse(text)
            except SyntaxError as exc:
                errors.append(f"Python syntax error in {path.relative_to(root)}: {exc}")
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text):
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                    continue
                local = unquote(target.split("#", 1)[0])
                if not local:
                    continue
                resolved = (path.parent / local).resolve()
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    errors.append(f"Broken/escaping local link in {path.relative_to(root)}: {target}")
    helper = ast.parse((skill / "scripts/researchflow.py").read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(helper):
        if isinstance(node, ast.Import):
            imports.update(x.name.split(".")[0] for x in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    if imports & {"subprocess", "socket", "urllib", "http", "requests", "ftplib"}:
        errors.append("Planning helper imports an execution/network module outside its scope")
    cases = json.loads((root / "evals/evals.json").read_text(encoding="utf-8"))
    ids = [x["id"] for x in cases["evals"]]
    if len(ids) < 12 or len(ids) != len(set(ids)) or any(not x["assertions"] for x in cases["evals"]):
        errors.append("Behavioral evaluation cases are missing or malformed")
    return errors


def main() -> int:
    try:
        errors = validate()
    except (OSError, ValueError, KeyError) as exc:
        errors = [str(exc)]
    for error in errors:
        print("ERROR:", error)
    if not errors:
        print("Package lint passed: structure, fixed stages, links, syntax, scope, and distribution inventory.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
