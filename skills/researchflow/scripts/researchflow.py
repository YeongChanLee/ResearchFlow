#!/usr/bin/env python3
"""Local document bookkeeping for ResearchFlow. No research execution or network I/O.

Receipts record claimed human confirmation; they do not authenticate a person.
Hashes bind records to content, not to scientific validity. Python 3.10+, stdlib only.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Any, Iterator

STAGES = (
    "Research Framing",
    "Literature Discovery & Workflow Reconstruction",
    "Data & Resource Co-design",
    "Methodology & Evaluation Design",
    "Specification Review & Baseline Approval",
)
STATUSES = {"pending", "in_progress", "awaiting_confirmation", "confirmed", "needs_reconfirmation"}
AVAILABILITY = {"unknown", "catalogue_only", "access_pending", "planned_collection", "verified_usable", "unavailable"}
ACCESS = {"metadata_only", "abstract_only", "full_text", "full_text_and_supplement", "user_provided", "unavailable"}
STATE_FIELDS = {"schema_version", "title", "research_mode", "created_at", "updated_at", "stages", "sources", "resources", "issues", "changes", "baseline"}
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
VERSION_RE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
PLACEHOLDER_RE = re.compile(r"\[TODO\]|\{\{[^\n]*?\}\}")
TEMPLATES = Path(__file__).resolve().parent.parent / "assets" / "templates"


class ResearchFlowError(ValueError):
    """An actionable input or consistency error."""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchFlowError(f"Cannot read JSON at {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    """Atomic replacement of a current working record (never a snapshot)."""
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        f.write(text)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def text_field(obj: dict[str, Any], key: str, *, nonempty: bool = True) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise ResearchFlowError(f"{key!r} must be a {'nonempty ' if nonempty else ''}string")
    return value


def date_field(obj: dict[str, Any], key: str) -> None:
    value = text_field(obj, key)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timezone is required")
    except ValueError as exc:
        raise ResearchFlowError(f"{key!r} must be an ISO timestamp with a timezone") from exc


def object_list(state: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = state.get(key)
    if not isinstance(items, list) or any(not isinstance(v, dict) for v in items):
        raise ResearchFlowError(f"{key!r} must be a list of objects")
    return items


def check_identity(record: dict[str, Any]) -> None:
    for key in ("researcher", "source", "quote"):
        value = text_field(record, key)
        if PLACEHOLDER_RE.search(value):
            raise ResearchFlowError(f"Approval {key} still contains a placeholder")
    date_field(record, "confirmed_at")


def validate_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ResearchFlowError("Receipt must be a JSON object")
    if type(receipt.get("stage")) is not int or receipt["stage"] not in range(1, 6):
        raise ResearchFlowError("Receipt stage must be an integer from 1 to 5")
    if receipt.get("decision") != "approve":
        raise ResearchFlowError("Receipt decision must be 'approve'")
    if not HASH_RE.fullmatch(text_field(receipt, "scope_sha256")):
        raise ResearchFlowError("Receipt scope_sha256 must be a SHA-256 hex digest")
    conditions = receipt.get("conditions")
    if not isinstance(conditions, list) or any(not isinstance(v, str) or not ID_RE.fullmatch(v) for v in conditions):
        raise ResearchFlowError("Receipt conditions must be a list of condition IDs")
    if len(set(conditions)) != len(conditions):
        raise ResearchFlowError("Duplicate condition IDs in receipt")
    check_identity(receipt)
    return receipt


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict) or set(state) != STATE_FIELDS:
        raise ResearchFlowError("State fields do not match schema version 1")
    if type(state["schema_version"]) is not int or state["schema_version"] != 1:
        raise ResearchFlowError("Unsupported state schema_version")
    text_field(state, "title")
    text_field(state, "research_mode")
    date_field(state, "created_at")
    date_field(state, "updated_at")
    stages = object_list(state, "stages")
    if len(stages) != 5:
        raise ResearchFlowError("Exactly five stages are required")
    for i, item in enumerate(stages, 1):
        if type(item.get("id")) is not int or item["id"] != i or item.get("name") != STAGES[i - 1]:
            raise ResearchFlowError(f"Stage {i} name/order is not the fixed ResearchFlow workflow")
        if not isinstance(item.get("status"), str) or item["status"] not in STATUSES:
            raise ResearchFlowError(f"Invalid status for Stage {i}")
        if item.get("approval") is not None:
            validate_receipt(item["approval"])
            if item["approval"]["stage"] != i:
                raise ResearchFlowError(f"Approval belongs to the wrong stage: {i}")
        if item["status"] == "confirmed" and not item.get("approval"):
            raise ResearchFlowError(f"Stage {i} claims confirmation without a receipt")
    all_ids: set[str] = set()
    for group in ("sources", "resources", "issues", "changes"):
        for item in object_list(state, group):
            identifier = text_field(item, "id")
            if not ID_RE.fullmatch(identifier) or identifier in all_ids:
                raise ResearchFlowError(f"Invalid or duplicate ID: {identifier}")
            all_ids.add(identifier)
    for item in state["sources"]:
        text_field(item, "citation")
        if not isinstance(item.get("access"), str) or item["access"] not in ACCESS or not isinstance(item.get("verification"), str) or item["verification"] not in {"verified", "unverified", "conflicting"}:
            raise ResearchFlowError(f"Invalid source evidence metadata: {item['id']}")
        text_field(item, "locator", nonempty=item["verification"] == "verified")
    for item in state["resources"]:
        text_field(item, "label")
        if type(item.get("required")) is not bool or not isinstance(item.get("availability"), str) or item["availability"] not in AVAILABILITY:
            raise ResearchFlowError(f"Invalid availability metadata: {item['id']}")
        text_field(item, "evidence", nonempty=item["availability"] == "verified_usable")
        text_field(item, "contingency", nonempty=False)
    for item in state["issues"]:
        text_field(item, "description")
        if not isinstance(item.get("gate"), str) or item["gate"] not in {"baseline", "execution", "advisory"} or not isinstance(item.get("status"), str) or item["status"] not in {"open", "resolved"}:
            raise ResearchFlowError(f"Invalid issue metadata: {item['id']}")
        if item["status"] == "resolved":
            text_field(item, "resolution")
    for item in state["changes"]:
        if not re.fullmatch(r"CR-[0-9]{3,}", item["id"]):
            raise ResearchFlowError("Change IDs must have the form CR-001")
        text_field(item, "trigger")
        affected = item.get("affected_stages")
        if not isinstance(affected, list) or not affected or any(type(i) is not int or i not in range(1, 6) for i in affected):
            raise ResearchFlowError(f"Invalid affected_stages: {item['id']}")
        if not isinstance(item.get("status"), str) or item["status"] not in {"proposed", "accepted", "implemented", "rejected"}:
            raise ResearchFlowError(f"Invalid change status: {item['id']}")
        if item["status"] in {"accepted", "implemented", "rejected"}:
            record = item.get("decision_record")
            if not isinstance(record, dict):
                raise ResearchFlowError(f"Change needs actual researcher decision_record: {item['id']}")
            check_identity(record)
    if state["baseline"] is not None:
        base = state["baseline"]
        if not isinstance(base, dict) or not VERSION_RE.fullmatch(str(base.get("version", ""))):
            raise ResearchFlowError("Invalid baseline record")
        if base.get("snapshot") != f"versions/v{base['version']}":
            raise ResearchFlowError("Baseline path must match the version")
    return state


def safe_root(project: Path) -> Path:
    path = project.expanduser()
    if path.is_symlink() or not path.is_dir():
        raise ResearchFlowError("Project must be an existing real directory, not a symlink")
    root = path.resolve()
    for entry in root.rglob("*"):
        if entry.is_symlink():
            raise ResearchFlowError(f"Symlinks are not allowed inside a managed project: {entry.relative_to(root)}")
    return root


def sections(root: Path) -> list[str]:
    try:
        content = (root / "research_spec.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ResearchFlowError(f"Cannot read research_spec.md: {exc}") from exc
    matches = list(re.finditer(r"^## ([1-5])\. (.+)$", content, flags=re.M))
    if len(matches) != 5 or any(m.group(1) != str(i) or m.group(2) != STAGES[i - 1] for i, m in enumerate(matches, 1)):
        raise ResearchFlowError("research_spec.md must contain the five exact ordered stage headings")
    return [content[m.start():matches[j + 1].start() if j < 4 else len(content)] for j, m in enumerate(matches)]


def supporting_files(root: Path, *, references_only: bool = False) -> list[Path]:
    result: list[Path] = []
    fixed = ["search_log.md"] if references_only else ["search_log.md", "decision_log.md"]
    for name in fixed:
        path = root / name
        if not path.is_file():
            raise ResearchFlowError(f"Required planning artifact is missing: {name}")
        result.append(path)
    directories = ("references",) if references_only else ("references", "changes")
    for name in directories:
        directory = root / name
        if not directory.is_dir():
            raise ResearchFlowError(f"Required planning directory is missing: {name}")
        result.extend(sorted(p for p in directory.rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".txt", ".bib"}))
    return result


def stage_scope(root: Path, state: dict[str, Any], stage: int) -> str:
    preamble = (root / "research_spec.md").read_text(encoding="utf-8").split("## 1. Research Framing", 1)[0]
    payload: dict[str, Any] = {"stage": stage, "title": state["title"], "research_mode": state["research_mode"], "preamble": preamble, "specification_sections": sections(root)[:stage]}
    if stage >= 2:
        payload["sources"] = state["sources"]
        payload["reference_files"] = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in supporting_files(root, references_only=True)}
    if stage >= 3:
        payload["resources"] = state["resources"]
    if stage >= 4:
        payload["issues"] = state["issues"]
    if stage == 5:
        payload["changes"] = state["changes"]
        payload["supporting_files"] = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in supporting_files(root)}
        # Final confirmation also binds the actual preceding confirmation records.
        payload["upstream_approvals"] = [s["approval"] for s in state["stages"][:4]]
    return digest(canonical(payload))


def current_confirmation(root: Path, state: dict[str, Any], stage: int) -> bool:
    return all(
        state["stages"][i - 1]["status"] == "confirmed"
        and bool(state["stages"][i - 1]["approval"])
        and state["stages"][i - 1]["approval"]["scope_sha256"] == stage_scope(root, state, i)
        for i in range(1, stage + 1)
    )


def condition_ids(state: dict[str, Any]) -> list[str]:
    return sorted([r["id"] for r in state["resources"] if r["required"] and r["availability"] not in {"verified_usable", "unavailable"}] + [i["id"] for i in state["issues"] if i["status"] == "open" and i["gate"] == "execution"])


def baseline_blockers(state: dict[str, Any]) -> list[str]:
    result = [f"Required resource unavailable: {r['id']}" for r in state["resources"] if r["required"] and r["availability"] == "unavailable"]
    result += [f"Baseline-level issue remains open: {i['id']}" for i in state["issues"] if i["status"] == "open" and i["gate"] == "baseline"]
    result += [f"Change is not resolved: {c['id']}" for c in state["changes"] if c["status"] not in {"implemented", "rejected"}]
    result += [f"Conditional resource lacks a contingency: {r['id']}" for r in state["resources"] if r["required"] and r["availability"] not in {"verified_usable", "unavailable"} and not r["contingency"].strip()]
    return result


def verify_snapshots(root: Path) -> list[str]:
    errors: list[str] = []
    directory = root / "versions"
    if not directory.is_dir():
        return ["versions/ directory is missing"]
    for snapshot in sorted(directory.iterdir()):
        if not snapshot.is_dir() or not snapshot.name.startswith("v") or not VERSION_RE.fullmatch(snapshot.name[1:]):
            errors.append(f"Unexpected entry in versions/: {snapshot.name}")
            continue
        try:
            manifest = read_json(snapshot / "snapshot_metadata.json")
            if not isinstance(manifest, dict) or manifest.get("version") != snapshot.name[1:]:
                raise ResearchFlowError("Snapshot version mismatch")
            hashes = manifest.get("files")
            if not isinstance(hashes, dict) or "research_spec.md" not in hashes or "project_state.json" not in hashes:
                raise ResearchFlowError("Incomplete snapshot manifest")
            for relative, expected in hashes.items():
                if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative:
                    raise ResearchFlowError("Unsafe snapshot manifest path")
                path = snapshot / relative
                if not isinstance(expected, str) or not HASH_RE.fullmatch(expected) or not path.is_file() or digest(path.read_bytes()) != expected:
                    errors.append(f"Snapshot content changed or missing: {snapshot.name}/{relative}")
            actual = {p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*") if p.is_file() and p.relative_to(snapshot).as_posix() != "snapshot_metadata.json"}
            if actual != set(hashes):
                errors.append(f"Snapshot file inventory changed: {snapshot.name}")
        except (ResearchFlowError, OSError) as exc:
            errors.append(f"Invalid snapshot {snapshot.name}: {exc}")
    return errors


def load_project(project: Path) -> tuple[Path, dict[str, Any]]:
    root = safe_root(project)
    state = validate_state(read_json(root / "project_state.json"))
    sections(root)
    supporting_files(root)
    return root, state


@contextmanager
def mutation_lock(root: Path) -> Iterator[None]:
    path = root / ".researchflow.lock"
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(now() + "\n")
    except FileExistsError as exc:
        raise ResearchFlowError("Project is locked; another edit may be in progress") from exc
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def save_state(root: Path, state: dict[str, Any], action: str, detail: Any) -> None:
    state["updated_at"] = now()
    validate_state(state)
    write_json(root / "project_state.json", state)
    # Diagnostic event log, not a signed, identity-verified or tamper-proof audit service.
    with (root / "audit.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at": now(), "action": action, "detail": detail}, ensure_ascii=False) + "\n")


def initialize(project: Path, title: str) -> Path:
    if not isinstance(title, str) or not title.strip() or "\n" in title or "\r" in title or PLACEHOLDER_RE.search(title):
        raise ResearchFlowError("Title must be a nonempty single line without placeholders")
    path = project.expanduser().absolute()
    if path.exists() or path.is_symlink():
        raise ResearchFlowError("Refusing to overwrite an existing project path")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".researchflow-init-", dir=path.parent))
    try:
        for name in ("research_spec.md", "project_state.json", "decision_log.md", "search_log.md"):
            content = (TEMPLATES / name).read_text(encoding="utf-8")
            if name == "project_state.json":
                state = json.loads(content)
                state["title"] = title.strip()
                state["created_at"] = state["updated_at"] = now()
                write_json(temporary / name, state)
            else:
                (temporary / name).write_text(content.replace("{{PROJECT_TITLE}}", title.strip()), encoding="utf-8")
        for directory in ("references", "changes", "versions"):
            (temporary / directory).mkdir()
        # Recheck immediately before rename; never intentionally replace an existing workspace.
        if path.exists() or path.is_symlink():
            raise ResearchFlowError("Destination appeared during initialization; refusing overwrite")
        temporary.rename(path)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return path


def check(project: Path, *, baseline_ready: bool = False) -> dict[str, Any]:
    root, state = load_project(project)
    errors = verify_snapshots(root)
    warnings: list[str] = []
    stage_results = []
    for i, content in enumerate(sections(root), 1):
        confirmed = current_confirmation(root, state, i)
        stage_results.append({"stage": i, "name": STAGES[i - 1], "current_confirmation": confirmed})
        if state["stages"][i - 1]["status"] == "confirmed" and not confirmed:
            errors.append(f"Stage {i} approval is stale; content or dependencies changed")
        if PLACEHOLDER_RE.search(content):
            (errors if baseline_ready or confirmed else warnings).append(f"Stage {i} contains unfilled placeholders")
        if baseline_ready and not confirmed:
            errors.append(f"Stage {i} lacks current explicit confirmation")
    blockers = baseline_blockers(state)
    if baseline_ready:
        errors.extend(blockers)
    else:
        warnings.extend(blockers)
    conditions = condition_ids(state)
    final_receipt = state["stages"][4]["approval"]
    if conditions and (baseline_ready or current_confirmation(root, state, 5)) and (not final_receipt or not set(conditions).issubset(set(final_receipt["conditions"]))):
        errors.append("Stage 5 approval does not acknowledge all condition IDs")
    if state["baseline"] is not None and not (root / state["baseline"]["snapshot"] / "snapshot_metadata.json").is_file():
        errors.append("Recorded approved baseline snapshot is missing")
    all_confirmed = all(s["current_confirmation"] for s in stage_results)
    readiness = "blocked" if blockers or errors else "awaiting_confirmation" if not all_confirmed else "conditional" if conditions else "ready_for_handoff"
    return {"ok": not errors, "readiness": readiness, "conditions": conditions, "stages": stage_results, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings)), "scope": "Bookkeeping only; not scientific validation or execution authorization."}


def approval_packet(project: Path, stage: int) -> dict[str, Any]:
    if stage not in range(1, 6):
        raise ResearchFlowError("Stage must be 1-5")
    root, state = load_project(project)
    return {"stage": stage, "name": STAGES[stage - 1], "scope_sha256": stage_scope(root, state, stage), "conditions": condition_ids(state) if stage == 5 else [], "prior_stages_current": all(current_confirmation(root, state, i) for i in range(1, stage)), "notice": "Present the scoped content to the researcher. This packet is not approval."}


def approve(project: Path, receipt: Any) -> dict[str, Any]:
    receipt = validate_receipt(receipt)
    root = safe_root(project)
    with mutation_lock(root):
        root, state = load_project(root)
        stage = receipt["stage"]
        if any(not current_confirmation(root, state, i) for i in range(1, stage)):
            raise ResearchFlowError("Earlier stages require current confirmation first")
        if receipt["scope_sha256"] != stage_scope(root, state, stage):
            raise ResearchFlowError("Receipt digest does not match current scoped content")
        if PLACEHOLDER_RE.search(sections(root)[stage - 1]):
            raise ResearchFlowError("Cannot confirm a stage containing unfilled placeholders")
        if stage == 5:
            blockers = baseline_blockers(state)
            if blockers:
                raise ResearchFlowError("Cannot approve baseline: " + "; ".join(blockers))
            if not set(condition_ids(state)).issubset(set(receipt["conditions"])):
                raise ResearchFlowError("Final receipt must acknowledge all condition IDs")
        state["stages"][stage - 1].update(status="confirmed", approval=receipt)
        for record in state["stages"][stage:]:
            if record["approval"] is not None:
                record["status"] = "needs_reconfirmation"
        save_state(root, state, "record_scoped_confirmation", receipt.copy())
    return {"recorded_stage": stage, "notice": "Receipt recorded; human identity and meaning of quote are not authenticated by this helper."}


def request_change(project: Path, identifier: str, stages: list[int], trigger: str) -> dict[str, Any]:
    if not re.fullmatch(r"CR-[0-9]{3,}", identifier) or not trigger.strip():
        raise ResearchFlowError("Use a safe CR-001 ID and a nonempty trigger")
    if not stages or any(type(i) is not int or i not in range(1, 6) for i in stages):
        raise ResearchFlowError("Affected stage must be 1-5")
    root = safe_root(project)
    with mutation_lock(root):
        root, state = load_project(root)
        if identifier in {item["id"] for group in ("sources", "resources", "issues", "changes") for item in state[group]}:
            raise ResearchFlowError("Change ID already exists")
        path = root / "changes" / f"{identifier}.md"
        if path.exists():
            raise ResearchFlowError("Refusing to overwrite a change-request file")
        affected = list(range(min(stages), 6))
        content = (TEMPLATES / "change-request.md").read_text(encoding="utf-8").replace("{{CHANGE_ID}}", identifier)
        content = content.replace("Trigger and supporting evidence:", "Trigger and supporting evidence: " + trigger)
        path.write_text(content, encoding="utf-8")
        state["changes"].append({"id": identifier, "trigger": trigger, "affected_stages": affected, "status": "proposed", "decision_record": None})
        for i in affected:
            if state["stages"][i - 1]["approval"] is not None:
                state["stages"][i - 1]["status"] = "needs_reconfirmation"
        save_state(root, state, "request_change", {"id": identifier, "affected_stages": affected})
    return {"change_request": identifier, "affected_stages": affected, "status": "proposed", "notice": "No scientific content was changed or approved."}


def snapshot(project: Path, version: str) -> dict[str, Any]:
    if not VERSION_RE.fullmatch(version):
        raise ResearchFlowError("Baseline version must be numeric MAJOR.MINOR.PATCH")
    root = safe_root(project)
    with mutation_lock(root):
        root, state = load_project(root)
        report = check(root, baseline_ready=True)
        if not report["ok"]:
            raise ResearchFlowError("Baseline not ready: " + "; ".join(report["errors"]))
        target = root / "versions" / f"v{version}"
        if target.exists():
            raise ResearchFlowError("Refusing to overwrite an existing baseline")
        old_versions = [tuple(map(int, p.name[1:].split("."))) for p in (root / "versions").iterdir() if p.is_dir() and VERSION_RE.fullmatch(p.name[1:])]
        if old_versions and tuple(map(int, version.split("."))) <= max(old_versions):
            raise ResearchFlowError("New baseline version must be greater than existing versions")
        files = [root / "research_spec.md", root / "project_state.json"] + supporting_files(root)
        if (root / "audit.jsonl").is_file():
            files.append(root / "audit.jsonl")
        temporary = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=root))
        metadata = {"version": version, "created_at": now(), "readiness": report["readiness"], "conditions": report["conditions"], "scope_sha256": stage_scope(root, state, 5), "files": {}}
        try:
            for source in files:
                relative = source.relative_to(root)
                destination = temporary / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                metadata["files"][relative.as_posix()] = digest(destination.read_bytes())
            write_json(temporary / "snapshot_metadata.json", metadata)
            temporary.rename(target)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        state["baseline"] = {"version": version, "snapshot": f"versions/v{version}", "readiness": report["readiness"], "approved_at": state["stages"][4]["approval"]["confirmed_at"]}
        save_state(root, state, "create_baseline_snapshot", {"version": version, "scope_sha256": metadata["scope_sha256"]})
    return {"snapshot": str(target), "version": version, "readiness": report["readiness"], "conditions": report["conditions"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Initialize a NEW planning directory")
    init.add_argument("project", type=Path)
    init.add_argument("--title", required=True)
    validate = commands.add_parser("check", help="Check document/state consistency")
    validate.add_argument("project", type=Path)
    validate.add_argument("--baseline-ready", action="store_true")
    packet = commands.add_parser("packet", help="Get a content-bound approval packet; does not approve")
    packet.add_argument("project", type=Path)
    packet.add_argument("--stage", type=int, choices=range(1, 6), required=True)
    record = commands.add_parser("approve", help="Record an ACTUAL researcher confirmation")
    record.add_argument("project", type=Path)
    record.add_argument("--receipt", type=Path, required=True)
    change = commands.add_parser("request-change", help="Propose a change; does not edit scientific content")
    change.add_argument("project", type=Path)
    change.add_argument("--id", required=True)
    change.add_argument("--stage", action="append", type=int, choices=range(1, 6), required=True)
    change.add_argument("--trigger", required=True)
    save = commands.add_parser("snapshot", help="Save a new approved baseline without overwriting")
    save.add_argument("project", type=Path)
    save.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = {"project": str(initialize(args.project, args.title)), "status": "draft"}
        elif args.command == "check":
            result = check(args.project, baseline_ready=args.baseline_ready)
        elif args.command == "packet":
            result = approval_packet(args.project, args.stage)
        elif args.command == "approve":
            result = approve(args.project, read_json(args.receipt))
        elif args.command == "request-change":
            result = request_change(args.project, args.id, args.stage, args.trigger)
        else:
            result = snapshot(args.project, args.version)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok", True) else 1
    except (ResearchFlowError, OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
