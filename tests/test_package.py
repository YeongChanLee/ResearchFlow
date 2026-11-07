"""Package, installer and publishing guards. No real host or GitHub writes."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_release
import install_skill
import package_common
import publish_github
import validate_package


class PackageTests(unittest.TestCase):
    def test_repository_lint(self):
        self.assertEqual(validate_package.validate(), [])

    def test_canonical_skill_install_to_custom_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "researchflow"
            installed = install_skill.install(destination)
            self.assertEqual((installed / "SKILL.md").read_bytes(), (install_skill.SOURCE / "SKILL.md").read_bytes())
            self.assertTrue((installed / "references/stage-2-literature.md").is_file())
            self.assertFalse(any(p.name == "__pycache__" for p in installed.rglob("*")))

    def test_installer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "researchflow"
            install_skill.install(destination)
            with self.assertRaises(ValueError):
                install_skill.install(destination)

    def test_installer_rejects_wrong_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                install_skill.install(Path(temporary) / "WrongName")

    def test_installer_source_symlink_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            try:
                source.symlink_to(install_skill.SOURCE, target_is_directory=True)
            except OSError:
                self.skipTest("Symlink creation unavailable")
            with self.assertRaises(ValueError):
                install_skill.install(Path(temporary) / "researchflow", source)

    def test_project_scoped_destinations(self):
        base = Path("/tmp/project").absolute()
        self.assertEqual(install_skill.destination_for("claude", base), base / ".claude/skills/researchflow")
        self.assertEqual(install_skill.destination_for("codex", base), base / ".agents/skills/researchflow")

    def test_distribution_inventory_excludes_private_and_caches(self):
        for path in package_common.distribution_files():
            relative = path.relative_to(ROOT)
            self.assertFalse(set(relative.parts) & {"private", "workspaces", "dist", ".git", "__pycache__"})
            self.assertNotIn(path.suffix, {".pdf", ".docx", ".pyc", ".pem", ".key"})

    def test_zip_root_layout_and_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = build_release.build(Path(temporary))
            with zipfile.ZipFile(paths[0]) as archive:
                names = archive.namelist()
                self.assertIn("researchflow/SKILL.md", names)
                self.assertIn("researchflow/LICENSE.txt", names)
                self.assertTrue(all(n.startswith("researchflow/") and ".." not in Path(n).parts for n in names))
                self.assertEqual(len(names), len(set(names)))
            with zipfile.ZipFile(paths[1]) as archive:
                self.assertIn("ResearchFlow/README.md", archive.namelist())
                self.assertIn("ResearchFlow/skills/researchflow/SKILL.md", archive.namelist())
                self.assertFalse(any("/.git/" in n or "/dist/" in n or "__pycache__" in n for n in archive.namelist()))

    def test_reproducible_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = build_release.build(Path(temporary) / "one")
            second = build_release.build(Path(temporary) / "two")
            self.assertEqual([p.read_bytes() for p in first], [p.read_bytes() for p in second])

    def test_checksum_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = build_release.build(Path(temporary))
            for line in paths[2].read_text().splitlines():
                expected, filename = line.split("  ")
                self.assertEqual(hashlib.sha256((Path(temporary) / filename).read_bytes()).hexdigest(), expected)

    def test_extracted_skill_helper_initializes_and_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = build_release.build(root / "dist")[0]
            with zipfile.ZipFile(archive) as zipped:
                zipped.extractall(root / "unpacked")
            spec = importlib.util.spec_from_file_location("installed_rf", root / "unpacked/researchflow/scripts/researchflow.py")
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            project = root / "smoke-project"
            module.initialize(project, "SYNTHETIC packaged-helper smoke test")
            self.assertTrue(module.check(project)["ok"])

    def test_publisher_dry_run_never_executes(self):
        with mock.patch.object(publish_github, "run", side_effect=AssertionError("No execution allowed")), mock.patch.object(publish_github, "execute", side_effect=AssertionError("No publication allowed")), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(publish_github.main(["--owner", "YeongChanLee"]), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result["repository"], "YeongChanLee/ResearchFlow")
        self.assertEqual(result["mode"], "dry_run")

    def test_publisher_owner_injection_rejected(self):
        with self.assertRaises(ValueError):
            publish_github.validate_owner("user; rm -rf /")
        with self.assertRaises(ValueError):
            publish_github.validate_owner("../other")

    def test_publisher_stops_without_tools(self):
        with mock.patch.object(publish_github.shutil, "which", return_value=None), mock.patch.object(publish_github, "run", side_effect=AssertionError("No command allowed")):
            with self.assertRaises(ValueError):
                publish_github.execute("YeongChanLee")

    def test_publisher_stops_on_wrong_authenticated_account(self):
        fake = mock.Mock(stdout="someone-else\n", returncode=0, stderr="")
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(publish_github.shutil, "which", return_value="/synthetic/bin/tool"), mock.patch.object(publish_github, "run", return_value=fake) as run:
            with self.assertRaises(ValueError):
                publish_github.execute("YeongChanLee", root=Path(temporary))
            self.assertEqual(run.call_count, 1)

    def test_publisher_existing_local_git_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(publish_github.shutil, "which", return_value="/synthetic/bin/tool"), mock.patch.object(publish_github, "run", side_effect=AssertionError("No calls allowed")):
            root = Path(temporary)
            (root / ".git").mkdir()
            with self.assertRaises(ValueError):
                publish_github.execute("YeongChanLee", root=root)
            self.assertTrue((root / ".git").is_dir())

    def test_behavioral_scenarios_are_not_claimed_as_model_runs(self):
        cases = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))
        self.assertEqual(cases["evaluation_status"], "not_run")
        self.assertEqual(len(cases["evals"]), 20)


if __name__ == "__main__":
    unittest.main()
