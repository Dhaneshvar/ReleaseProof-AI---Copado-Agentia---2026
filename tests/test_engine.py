import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from backend.agentia_adapter import AgentiaAdapter, outcome, public_data
from backend.api import dispatch
from backend.demo_runner import digest
from backend.engine import ReleaseService
from backend.store import Store


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "test.sqlite3"
        self.service = ReleaseService(Store(self.path))

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self, scenario="boundary_bug", **kwargs):
        return self.service.analyze({"scenario": scenario, **kwargs})

    def run_checks(self, a):
        job = self.service.start_run(a["id"], a["version"], background=False)
        self.assertEqual(job["status"], "completed", job)
        return self.service.get(a["id"])

    def change(self, a, action, **kwargs):
        return self.service.mutate(a["id"], {"action": action, "expected_version": a["version"], **kwargs})

    def test_green_baseline_does_not_verify_requirements(self):
        a = self.analyze()
        self.assertTrue(all(c["status"] == "passed" for c in a["baseline"]))
        self.assertEqual(a["decision"]["state"], "insufficient")
        a = self.run_checks(a)
        self.assertEqual(a["decision"]["state"], "blocked")
        boundary = next(c for c in a["checks"] if c["id"] == "AC-2")
        self.assertEqual(boundary["result"]["actual"], "Senior Sales")
        self.assertEqual(boundary["result"]["expected"], "Standard Sales")

    def test_fix_invalidates_then_selectively_rechecks(self):
        a = self.run_checks(self.analyze())
        a = self.change(a, "fix_boundary")
        self.assertEqual(a["decision"]["state"], "stale")
        self.assertEqual({c["id"] for c in a["recheck_plan"]}, {"AC-1", "AC-2"})
        a = self.run_checks(a)
        self.assertEqual(a["decision"]["state"], "satisfied")
        self.assertEqual(len(a["runs"][-1]["selected"]), 2)

    def test_permission_drift_does_not_invalidate_independent_boundary(self):
        a = self.run_checks(self.analyze("correct"))
        old_bundle = self.service.bundle(a["id"])
        a = self.change(a, "revoke_permission")
        self.assertEqual([c["id"] for c in a["recheck_plan"]], ["REG-INC-1042"])
        verified = self.service.verify(old_bundle)
        self.assertEqual(verified["freshness"], "stale")
        self.assertFalse(verified["valid"])
        a = self.run_checks(a)
        self.assertEqual(a["decision"]["state"], "blocked")

    def test_missing_permission_selected_by_incident(self):
        a = self.run_checks(self.analyze("permission_bug"))
        self.assertEqual(a["summary"]["failed"], 1)
        self.assertEqual(a["incidents"][0]["id"], "INC-1042")
        self.assertIn("Lead_Routing.permissionset", a["incidents"][0]["matched_components"])

    def test_unrelated_change_does_not_select_incident(self):
        a = self.run_checks(self.analyze("unrelated"))
        self.assertEqual(a["incidents"], [])
        self.assertEqual(a["summary"]["total"], 4)

    def test_unrelated_notes_do_not_invalidate_evidence(self):
        a = self.run_checks(self.analyze("correct"))
        old = self.service.bundle(a["id"])
        a = self.change(a, "unrelated_change")
        self.assertEqual(a["decision"]["state"], "satisfied")
        self.assertTrue(self.service.verify(old)["valid"])

    def test_environment_change_invalidates_every_claim(self):
        a = self.run_checks(self.analyze("correct"))
        a = self.change(a, "change_environment", environment="PROD")
        self.assertEqual(a["summary"]["stale"], a["summary"]["total"])
        self.assertEqual(a["decision"]["state"], "stale")

    def test_outage_cannot_pass(self):
        a = self.run_checks(self.analyze("unavailable"))
        self.assertEqual(a["summary"]["passed"], 0)
        self.assertEqual(a["decision"]["state"], "insufficient")

    def test_arbitrary_threshold_not_hardcoded(self):
        a = self.run_checks(self.analyze(threshold=117, work_item_id="US-999"))
        boundary = next(c for c in a["checks"] if c["id"] == "AC-2")
        self.assertEqual(boundary["result"]["input"], "score = 117")
        self.assertEqual(boundary["status"], "failed")

    def test_tampered_bundle_detected_even_with_recomputed_checksum(self):
        a = self.run_checks(self.analyze("correct"))
        bundle = self.service.bundle(a["id"])
        self.assertTrue(self.service.verify(bundle)["valid"])
        bundle["analysis"]["title"] = "Changed"
        self.assertFalse(self.service.verify(bundle)["integrity"])
        bundle["sha256"] = digest(bundle["analysis"])
        self.assertFalse(self.service.verify(bundle)["matches_local_record"])
        self.assertFalse(self.service.verify(bundle)["valid"])

    def test_history_persists_and_comparison_is_real(self):
        a = self.run_checks(self.analyze())
        service = ReleaseService(Store(self.path))
        self.assertEqual(service.get(a["id"])["decision"]["state"], "blocked")
        diff = service.compare(a["id"], 1)
        self.assertEqual(diff["from_decision"], "insufficient")
        self.assertEqual(len(diff["changes"]), 5)

    def test_imported_incident_is_persistent_and_adds_obligation(self):
        incident = {"id": "INC-9", "title": "Boundary regression", "root_cause": "Comparator", "actor": "Routing service",
                    "components": ["LeadScoreRouter.model"], "regression_kind": "boundary", "reviewed": True, "provenance": "Synthetic test"}
        self.service.import_incident(incident)
        service = ReleaseService(Store(self.path))
        a = service.analyze({})
        self.assertIn("REG-INC-9", [c["id"] for c in a["checks"]])

    def test_optimistic_lock_and_duplicate_run(self):
        a = self.analyze()
        self.change(a, "fix_boundary")
        with self.assertRaises(ValueError):
            self.service.start_run(a["id"], a["version"], background=False)
        a = self.service.get(a["id"])
        self.service.store.put_job({"id": "RUN-ACTIVE", "analysis_id": a["id"], "status": "running"})
        with self.assertRaises(ValueError):
            self.change(a, "fix_boundary")
        with self.assertRaises(ValueError):
            self.service.start_run(a["id"], a["version"], background=False)

    def test_restart_interrupts_unfinished_jobs(self):
        self.service.store.put_job({"id": "RUN-INT", "analysis_id": "RP-X", "status": "running"})
        self.service.store.recover_jobs()
        self.assertEqual(self.service.store.job("RUN-INT")["status"], "interrupted")

    def test_live_unknown_assertions_never_pass_from_job_success(self):
        adapter = Mock()
        adapter.collect.return_value = {"story": {"title": "Actual work", "acceptanceCriteria": "Route leads"}, "dependencies": [], "revision": "abc", "warnings": []}
        adapter.run_live.return_value = [{"name": "CRT", "status": "passed"}]
        self.service.adapter = adapter
        a = self.run_checks(self.service.analyze({"mode": "live"}))
        self.assertEqual(a["decision"]["state"], "insufficient")
        self.assertEqual(a["summary"]["passed"], 0)
        self.assertEqual(a["incidents"], [])

    def test_live_failure_does_not_fallback_to_demo(self):
        self.service.adapter = Mock()
        self.service.adapter.collect.side_effect = ValueError("Unavailable")
        with self.assertRaises(ValueError):
            self.service.analyze({"mode": "live"})
        self.assertEqual(self.service.store.list(), [])

    def test_status_parsing_is_conservative(self):
        for status in ["unavailable", "complete", "finished", "", "queued"]:
            self.assertEqual(outcome({"status": status}), "unverified")
        self.assertEqual(outcome({"result": {"status": "failed"}}), "failed")
        self.assertEqual(outcome({"data": {"status": "passed"}}), "passed")
        self.assertEqual(public_data({"token": "SECRET", "name": "check"}), {"name": "check"})

    def test_input_and_api_validation(self):
        for payload in [{"environment": "anything"}, {"threshold": True}, {"threshold": 0}, {"work_item_id": "US-1 & echo hello"}, {"mode": "guess"}]:
            with self.assertRaises(ValueError):
                self.service.analyze(payload)
        with self.assertRaises(KeyError):
            dispatch(self.service, "GET", "/api/no-such-route")
        self.assertEqual(dispatch(self.service, "GET", "/api/health")["version"], "0.3.0")


if __name__ == "__main__":
    unittest.main()
