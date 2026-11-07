#!/usr/bin/env python3
"""Build deterministic source/skill ZIPs from the explicit public-file inventory."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from package_common import ROOT, distribution_files
from validate_package import validate


def write_zip(path: Path, files: list[Path], source_root: Path, prefix: str) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for file in sorted(files):
            name = prefix + "/" + file.relative_to(source_root).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 5, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, file.read_bytes(), compresslevel=9)


def build(output: Path | None = None, root: Path = ROOT) -> list[Path]:
    errors = validate(root)
    if errors:
        raise ValueError("Cannot package invalid source: " + "; ".join(errors))
    output = output or root / "dist"
    output.mkdir(parents=True, exist_ok=True)
    version = (root / "VERSION").read_text().strip()
    files = distribution_files(root)
    skill = root / "skills/researchflow"
    skill_files = [p for p in files if p.is_relative_to(skill)]
    skill_zip = output / f"researchflow-skill-{version}.zip"
    source_zip = output / f"ResearchFlow-source-{version}.zip"
    write_zip(skill_zip, skill_files, skill, "researchflow")
    write_zip(source_zip, files, root, "ResearchFlow")
    sums = output / "SHA256SUMS.txt"
    sums.write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in (skill_zip, source_zip)), encoding="utf-8")
    return [skill_zip, source_zip, sums]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        for path in build(args.output):
            print(path)
        return 0
    except (ValueError, OSError) as exc:
        print(f"Build stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
