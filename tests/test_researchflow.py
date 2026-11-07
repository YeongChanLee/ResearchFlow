"""All approval/evidence examples in this suite are SYNTHETIC fixtures, not research."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rf", ROOT / "skills/researchflow/scripts/researchflow.py")
assert SPEC and SPEC.loader
rf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rf)


class ResearchFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name) / "project"
        rf.initialize(self.project, 'Synthetic research fixture — "검증"')

    def tearDown(self):
        self.tmp.cleanup()

    def state(self):
        return rf.read_json(self.project / "project_state.json")

    def save(self, state):
        rf.write_json(self.project / "project_state.json", state)

    def fill(self):
        path = self.project / "research_spec.md"
        path.write_text(path.read_text(encoding="utf-8").replace("[TODO]", "Synthetic fixture specification:"), encoding="utf-8")

    def receipt(self, stage, conditions=None):
        packet = rf.approval_packet(self.project, stage)
        return {"stage": stage, "decision": "approve", "scope_sha256": packet["scope_sha256"], "researcher": "SYNTHETIC TEST RESEARCHER", "confirmed_at": rf.now(), "source": f"synthetic-test:stage-{stage}", "quote": f"SYNTHETIC FIXTURE: I approve the displayed Stage {stage} content and listed conditions.", "conditions": packet["conditions"] if conditions is None else conditions}

    def approve_all(self):
        self.fill()
        for i in range(1, 6):
            rf.approve(self.project, self.receipt(i))

    def resource(self, availability="access_pending", required=True):
        return {"id": "RES-001", "label": "SYNTHETIC resource", "required": required, "availability": availability, "evidence": "synthetic-test:availability" if availability == "verified_usable" else "", "contingency": "SYNTHETIC alternative acquisition plan"}

    def edit_stage(self, stage):
        path = self.project / "research_spec.md"
        old = f"## {stage}. {rf.STAGES[stage-1]}"
        path.write_text(path.read_text(encoding="utf-8").replace(old, old + "\n\nSYNTHETIC amendment."), encoding="utf-8")

    def test_init_keeps_unicode_and_quotes(self):
        self.assertIn('"검증"', self.state()["title"])
        self.assertIn('"검증"', (self.project / "research_spec.md").read_text(encoding="utf-8"))

    def test_init_refuses_existing_directory(self):
        with self.assertRaises(rf.ResearchFlowError):
            rf.initialize(self.project, "replacement")

    def test_init_refuses_empty_title(self):
        with self.assertRaises(rf.ResearchFlowError):
            rf.initialize(Path(self.tmp.name) / "new", " ")

    def test_init_refuses_multiline_title(self):
        with self.assertRaises(rf.ResearchFlowError):
            rf.initialize(Path(self.tmp.name) / "new", "x\n## 1. injected")

    def test_draft_check_passes_with_warnings(self):
        report = rf.check(self.project)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["warnings"]), 5)
        self.assertEqual(report["readiness"], "awaiting_confirmation")

    def test_draft_not_baseline_ready(self):
        self.assertFalse(rf.check(self.project, baseline_ready=True)["ok"])

    def test_packet_does_not_mutate_state(self):
        before = (self.project / "project_state.json").read_bytes()
        rf.approval_packet(self.project, 1)
        self.assertEqual(before, (self.project / "project_state.json").read_bytes())

    def test_reject_placeholder_approval(self):
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(1))

    def test_reject_skipping_stage(self):
        self.fill()
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(2))

    def test_reject_empty_approval_source(self):
        self.fill()
        receipt = self.receipt(1)
        receipt["source"] = ""
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_reject_missing_quote(self):
        self.fill()
        receipt = self.receipt(1)
        del receipt["quote"]
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_reject_placeholder_researcher(self):
        self.fill()
        receipt = self.receipt(1)
        receipt["researcher"] = "[TODO]"
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_reject_receipt_with_changed_scope(self):
        self.fill()
        receipt = self.receipt(1)
        self.edit_stage(1)
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_reject_timezone_free_receipt(self):
        self.fill()
        receipt = self.receipt(1)
        receipt["confirmed_at"] = "2026-11-05T12:00:00"
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_reject_wrong_decision(self):
        self.fill()
        receipt = self.receipt(1)
        receipt["decision"] = "continue drafting"
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, receipt)

    def test_confirmed_stage_records_receipt_and_audit(self):
        self.fill()
        receipt = self.receipt(1)
        rf.approve(self.project, receipt)
        self.assertEqual(self.state()["stages"][0]["approval"], receipt)
        event = json.loads((self.project / "audit.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(event["detail"]["quote"], receipt["quote"])

    def test_all_stages_approved_ready(self):
        self.approve_all()
        report = rf.check(self.project, baseline_ready=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["readiness"], "ready_for_handoff")

    def test_stage4_edit_preserves_earlier_approvals(self):
        self.approve_all()
        self.edit_stage(4)
        report = rf.check(self.project)
        self.assertFalse(report["ok"])
        self.assertEqual([x["current_confirmation"] for x in report["stages"]], [True, True, True, False, False])

    def test_upstream_edit_invalidates_all_downstream(self):
        self.approve_all()
        self.edit_stage(1)
        self.assertTrue(all(not x["current_confirmation"] for x in rf.check(self.project)["stages"]))

    def test_preamble_edit_invalidates_approvals(self):
        self.approve_all()
        path = self.project / "research_spec.md"
        path.write_text("New assumption\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
        self.assertFalse(rf.check(self.project)["stages"][0]["current_confirmation"])

    def test_reference_file_change_invalidates_stage2_and_later(self):
        self.approve_all()
        (self.project / "references/new.md").write_text("SYNTHETIC evidence change", encoding="utf-8")
        statuses = [x["current_confirmation"] for x in rf.check(self.project)["stages"]]
        self.assertEqual(statuses, [True, False, False, False, False])

    def test_resource_metadata_change_invalidates_stage3_and_later(self):
        self.approve_all()
        state = self.state()
        state["resources"].append(self.resource("verified_usable"))
        self.save(state)
        self.assertEqual([x["current_confirmation"] for x in rf.check(self.project)["stages"]], [True, True, False, False, False])

    def test_decision_log_change_invalidates_final_approval(self):
        self.approve_all()
        with (self.project / "decision_log.md").open("a") as out:
            out.write("SYNTHETIC changed decision\n")
        self.assertEqual([x["current_confirmation"] for x in rf.check(self.project)["stages"]], [True, True, True, True, False])

    def test_required_unavailable_resource_blocks_baseline(self):
        self.fill()
        state = self.state(); state["resources"].append(self.resource("unavailable")); self.save(state)
        for i in range(1, 5):
            rf.approve(self.project, self.receipt(i))
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(5))

    def test_optional_unavailable_resource_does_not_automatically_block(self):
        state = self.state(); state["resources"].append(self.resource("unavailable", required=False)); self.save(state)
        self.approve_all()
        self.assertTrue(rf.check(self.project, baseline_ready=True)["ok"])

    def test_pending_access_requires_conditional_acknowledgement(self):
        self.fill()
        state = self.state(); state["resources"].append(self.resource()); self.save(state)
        for i in range(1, 5):
            rf.approve(self.project, self.receipt(i))
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(5, conditions=[]))
        rf.approve(self.project, self.receipt(5))
        report = rf.check(self.project, baseline_ready=True)
        self.assertEqual(report["readiness"], "conditional")
        self.assertTrue(report["ok"])

    def test_conditional_resource_requires_contingency(self):
        self.fill()
        state = self.state(); resource = self.resource(); resource["contingency"] = ""; state["resources"].append(resource); self.save(state)
        for i in range(1, 5):
            rf.approve(self.project, self.receipt(i))
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(5))

    def test_verified_usable_requires_evidence(self):
        state = self.state(); resource = self.resource("verified_usable"); resource["evidence"] = ""; state["resources"].append(resource); self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_open_baseline_issue_blocks(self):
        self.fill()
        state = self.state(); state["issues"].append({"id": "ISS-001", "description": "SYNTHETIC design contradiction", "status": "open", "gate": "baseline"}); self.save(state)
        for i in range(1, 5):
            rf.approve(self.project, self.receipt(i))
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(5))

    def test_open_execution_issue_is_condition(self):
        state = self.state(); state["issues"].append({"id": "ISS-001", "description": "SYNTHETIC external approval pending", "status": "open", "gate": "execution"}); self.save(state)
        self.approve_all()
        self.assertEqual(rf.check(self.project)["conditions"], ["ISS-001"])

    def test_resolved_issue_needs_resolution(self):
        state = self.state(); state["issues"].append({"id": "ISS-001", "description": "SYNTHETIC issue", "status": "resolved", "gate": "execution"}); self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_snapshot_captures_hashes_and_preserves_draft(self):
        self.approve_all()
        before = (self.project / "research_spec.md").read_bytes()
        result = rf.snapshot(self.project, "1.0.0")
        target = Path(result["snapshot"])
        self.assertEqual((target / "research_spec.md").read_bytes(), before)
        self.assertIn("audit.jsonl", rf.read_json(target / "snapshot_metadata.json")["files"])
        self.assertTrue(rf.check(self.project, baseline_ready=True)["ok"])

    def test_snapshot_refuses_overwrite(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        with self.assertRaises(rf.ResearchFlowError):
            rf.snapshot(self.project, "1.0.0")

    def test_snapshot_version_must_increase(self):
        self.approve_all(); rf.snapshot(self.project, "2.0.0")
        with self.assertRaises(rf.ResearchFlowError):
            rf.snapshot(self.project, "1.0.0")

    def test_snapshot_rejects_traversal_version(self):
        self.approve_all()
        with self.assertRaises(rf.ResearchFlowError):
            rf.snapshot(self.project, "../escape")

    def test_modified_snapshot_detected(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        (self.project / "versions/v1.0.0/research_spec.md").write_text("tampered", encoding="utf-8")
        self.assertFalse(rf.check(self.project)["ok"])

    def test_added_snapshot_file_detected(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        (self.project / "versions/v1.0.0/extra.md").write_text("added", encoding="utf-8")
        self.assertFalse(rf.check(self.project)["ok"])

    def test_snapshot_manifest_traversal_rejected(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        path = self.project / "versions/v1.0.0/snapshot_metadata.json"
        manifest = rf.read_json(path); manifest["files"]["../../escape"] = "0"*64; rf.write_json(path, manifest)
        self.assertFalse(rf.check(self.project)["ok"])

    def test_missing_recorded_snapshot_detected(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        shutil.rmtree(self.project / "versions/v1.0.0")
        self.assertFalse(rf.check(self.project)["ok"])

    def test_change_only_proposes_and_marks_affected_scope(self):
        self.approve_all()
        before = (self.project / "research_spec.md").read_bytes()
        result = rf.request_change(self.project, "CR-001", [3], "SYNTHETIC data failure")
        self.assertEqual(result["affected_stages"], [3, 4, 5])
        self.assertEqual(before, (self.project / "research_spec.md").read_bytes())
        self.assertEqual(self.state()["changes"][0]["status"], "proposed")
        self.assertEqual([s["status"] for s in self.state()["stages"]], ["confirmed", "confirmed", "needs_reconfirmation", "needs_reconfirmation", "needs_reconfirmation"])

    def test_duplicate_change_refused(self):
        rf.request_change(self.project, "CR-001", [3], "SYNTHETIC")
        with self.assertRaises(rf.ResearchFlowError):
            rf.request_change(self.project, "CR-001", [3], "SYNTHETIC again")

    def test_change_id_path_traversal_refused(self):
        with self.assertRaises(rf.ResearchFlowError):
            rf.request_change(self.project, "../../bad", [3], "SYNTHETIC")

    def test_unresolved_change_blocks_final_confirmation(self):
        self.approve_all()
        rf.request_change(self.project, "CR-001", [3], "SYNTHETIC")
        for i in (3, 4):
            rf.approve(self.project, self.receipt(i))
        with self.assertRaises(rf.ResearchFlowError):
            rf.approve(self.project, self.receipt(5))

    def test_change_resolution_requires_researcher_record(self):
        rf.request_change(self.project, "CR-001", [3], "SYNTHETIC")
        state = self.state(); state["changes"][0]["status"] = "implemented"; self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_full_agile_amendment_preserves_old_baseline(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        previous = (self.project / "versions/v1.0.0/research_spec.md").read_bytes()
        rf.request_change(self.project, "CR-001", [3], "SYNTHETIC resource unavailable")
        self.edit_stage(3)
        state = self.state()
        state["changes"][0].update(status="implemented", decision_record={"researcher": "SYNTHETIC TEST RESEARCHER", "confirmed_at": rf.now(), "source": "synthetic-test:change", "quote": "SYNTHETIC FIXTURE: I approve the described resource redesign."})
        state["resources"].append(self.resource("verified_usable"))
        self.save(state)
        for i in (3, 4, 5):
            rf.approve(self.project, self.receipt(i))
        rf.snapshot(self.project, "1.1.0")
        self.assertEqual(previous, (self.project / "versions/v1.0.0/research_spec.md").read_bytes())
        self.assertNotEqual(previous, (self.project / "versions/v1.1.0/research_spec.md").read_bytes())
        self.assertTrue(rf.check(self.project, baseline_ready=True)["ok"])

    def test_fixed_stage_order_enforced(self):
        state = self.state(); state["stages"].reverse(); self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_heading_name_enforced(self):
        path = self.project / "research_spec.md"
        path.write_text(path.read_text(encoding="utf-8").replace("## 1. Research Framing", "## 1. Execute Research"), encoding="utf-8")
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_unrecorded_confirmed_status_rejected(self):
        state = self.state(); state["stages"][0]["status"] = "confirmed"; self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_invalid_state_type_fails_clearly(self):
        state = self.state(); state["stages"][0]["status"] = []; self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_duplicate_resource_ids_rejected(self):
        state = self.state(); state["resources"] = [self.resource(), self.resource()]; self.save(state)
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_symlink_inside_project_rejected(self):
        target = Path(self.tmp.name) / "outside.txt"; target.write_text("outside", encoding="utf-8")
        try:
            (self.project / "references/link.txt").symlink_to(target)
        except OSError:
            self.skipTest("Symlink creation unavailable")
        with self.assertRaises(rf.ResearchFlowError):
            rf.check(self.project)

    def test_lock_prevents_concurrent_mutation(self):
        self.fill()
        with rf.mutation_lock(self.project):
            with self.assertRaises(rf.ResearchFlowError):
                rf.approve(self.project, self.receipt(1))

    def test_integrity_failure_never_claims_handoff_readiness(self):
        self.approve_all(); rf.snapshot(self.project, "1.0.0")
        (self.project / "versions/v1.0.0/research_spec.md").write_text("tampered", encoding="utf-8")
        self.assertEqual(rf.check(self.project)["readiness"], "blocked")

    def test_normal_check_detects_missing_final_condition_acknowledgement(self):
        state = self.state(); state["resources"].append(self.resource()); self.save(state)
        self.approve_all()
        state = self.state(); state["stages"][4]["approval"]["conditions"] = []; self.save(state)
        self.assertFalse(rf.check(self.project)["ok"])

    def test_downstream_confirmation_depends_on_prior_confirmation_status(self):
        self.approve_all()
        state = self.state(); state["stages"][0]["status"] = "needs_reconfirmation"; self.save(state)
        self.assertTrue(all(not row["current_confirmation"] for row in rf.check(self.project)["stages"]))

    def test_cli_json_error_and_nonzero_exit(self):
        with contextlib.redirect_stderr(io.StringIO()) as error:
            code = rf.main(["check", str(Path(self.tmp.name) / "missing")])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(error.getvalue())["ok"])

    def test_cli_baseline_not_ready_nonzero(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = rf.main(["check", str(self.project), "--baseline-ready"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
