"""Release contracts, execution, decision policy, and evidence lifecycle.

Demo results come from executable local models. Live facts remain unverified until
their requirement, revision, persona and target can be bound to runner assertions.
"""
from __future__ import annotations

import copy
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

from .agentia_adapter import AgentiaAdapter
from .demo_runner import baseline, digest, execute, snapshot
from .store import Store

POLICY = "all-required-checks-current-v1"
ENVIRONMENTS = {"DEV", "QA", "UAT", "PROD"}
SCENARIOS = {
    "boundary_bug": {"label": "Passing tests, missed boundary", "inclusive": True, "permission": True},
    "correct": {"label": "Correct implementation", "inclusive": False, "permission": True},
    "permission_bug": {"label": "Missing standard-user permission", "inclusive": False, "permission": False},
    "unrelated": {"label": "Routing without incident component overlap", "inclusive": False, "permission": True},
    "unavailable": {"label": "Unavailable test runner", "inclusive": False, "permission": True},
}
SEED_INCIDENT = {
    "id": "INC-1042", "title": "Standard users could not access Lead routing",
    "components": ["Lead_Routing.flow", "Lead_Routing.permissionset"],
    "root_cause": "Required Lead access was omitted from the standard-user permission set.",
    "regression_kind": "permission", "actor": "Standard Sales", "reviewed": True,
    "provenance": "Synthetic hackathon incident; not customer production data.", "synthetic": True,
}


def now():
    return datetime.now(timezone.utc).isoformat()


def identifier(value, label="identifier"):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ValueError(f"Invalid {label}")
    return value


def environment(value):
    if value not in ENVIRONMENTS:
        raise ValueError("Environment must be DEV, QA, UAT or PROD")
    return value


def make_check(cid, title, kind, actor, dependencies, source, reason):
    return {"id": cid, "title": title, "kind": kind, "actor": actor, "dependencies": dependencies,
            "source": source, "reason": reason, "status": "unverified", "result": None, "stale_reason": None}


def evaluate(analysis):
    checks = analysis["checks"]
    for check in checks:
        result = check.get("result")
        if result:
            changed = [key for key, value in result["input_hashes"].items() if analysis["snapshot"]["parts"].get(key) != value]
            if changed:
                check.update(status="stale", stale_reason="Changed: " + ", ".join(changed))
    failed = [c for c in checks if c["status"] == "failed"]
    stale = [c for c in checks if c["status"] == "stale"]
    missing = [c for c in checks if c["status"] not in {"passed", "failed", "stale"}]
    live_failures = [r for r in analysis.get("live_results", []) if r["status"] == "failed"]
    if failed or live_failures:
        state, title = "blocked", "Release blocked"
        reason = failed[0]["title"] + " does not match the required behavior." if failed else "An Agentia check failed."
    elif stale:
        state, title, reason = "stale", "Evidence needs a recheck", f"{len(stale)} check(s) no longer match the current inputs."
    elif missing or not checks or analysis["mode"] == "live":
        state, title, reason = "insufficient", "Evidence incomplete", "Execute required checks to establish the stated behavior."
        if analysis["mode"] == "live":
            reason = "Live business assertions and target snapshots are not mapped. Runner success alone cannot verify these requirements."
    else:
        state, title, reason = "satisfied", "Evidence requirements satisfied", "All modeled obligations have current passing results. Human approval is still required."
    analysis["decision"] = {"state": state, "title": title, "reason": reason, "policy": POLICY,
                            "approval": "not_requested", "scope": "Local model only" if analysis["mode"] == "demo" else "Copado evidence collection"}
    analysis["summary"] = {"passed": sum(c["status"] == "passed" for c in checks), "failed": len(failed),
                           "stale": len(stale), "unverified": len(missing), "total": len(checks)}
    analysis["recheck_plan"] = [{"id": c["id"], "title": c["title"], "reason": c.get("stale_reason") or c["reason"]}
                                for c in checks if c["status"] != "passed"]
    analysis["graph"] = {
        "nodes": [{"id": "story", "label": analysis["work_item_id"], "kind": "requirement"}]
                 + [{"id": c["id"], "label": c["title"], "kind": "check", "status": c["status"]} for c in checks]
                 + [{"id": i["id"], "label": i["title"], "kind": "incident"} for i in analysis["incidents"]],
        "edges": [{"from": c["source"], "to": c["id"], "relationship": "requires", "reason": c["reason"]} for c in checks],
    }
    return analysis


class ReleaseService:
    def __init__(self, store=None, adapter=None, recover=False):
        self.store = store or Store()
        self.adapter = adapter or AgentiaAdapter()
        self.lock = threading.RLock()
        if recover:
            self.store.recover_jobs()
        self.store.put_incident(SEED_INCIDENT, seed=True)

    def analyze(self, payload):
        work_item = identifier(payload.get("work_item_id", "US-247"), "work item")
        target = environment(payload.get("environment", "UAT"))
        mode = payload.get("mode", "demo")
        if mode not in {"demo", "live"}:
            raise ValueError("Choose explicit demo or live mode")
        analysis = {"schema_version": 1, "id": "RP-" + uuid.uuid4().hex[:12].upper(), "version": 0,
                    "work_item_id": work_item, "environment": target, "mode": mode, "created_at": now(),
                    "updated_at": now(), "runs": [], "events": [], "checks": [], "incidents": [], "warnings": [], "live_results": []}
        if mode == "demo":
            scenario = payload.get("scenario", "boundary_bug")
            if scenario not in SCENARIOS:
                raise ValueError("Unknown demo scenario")
            threshold = payload.get("threshold", 80)
            if type(threshold) is not int or not 1 <= threshold <= 999:
                raise ValueError("Demo score threshold must be an integer from 1 to 999")
            config = {**SCENARIOS[scenario], "threshold": threshold, "scenario": scenario, "notes_revision": 0}
            analysis.update(title="Lead routing contract", config=config,
                            components=["LeadScoreRouter.model"] + ([] if scenario == "unrelated" else ["Lead_Routing.flow", "Lead_Routing.permissionset"]),
                            requirements=f"Integer Lead scores greater than {threshold} route to Senior Sales; all others route to Standard Sales. Only Sales Managers can override routing.",
                            baseline=baseline(config), runner="Executable Python reference model",
                            limitations=["Synthetic scenario; no Apex, Salesforce org, or Copado job is executed.", "Deterministic reviewed templates; no LLM interpretation is claimed.", "Evidence covers the listed checks only and does not authorize deployment."])
            common = ["requirements", "tests", "environment", "policy"]
            analysis["checks"] = [
                make_check("AC-1", f"Score {threshold + 1} routes to Senior Sales", "high", "Routing service", ["routing", *common], "story", "Upper boundary of the approved integer-score contract."),
                make_check("AC-2", f"Score {threshold} stays in Standard Sales", "boundary", "Routing service", ["routing", *common], "story", "Equality must not satisfy a strict greater-than requirement."),
                make_check("AC-3", "Standard users cannot override routing", "override", "Standard Sales", ["authorization", *common], "story", "Verify the negative authorization requirement."),
                make_check("AC-4", "Sales Managers can override routing", "override", "Sales Manager", ["authorization", *common], "story", "Verify the allowed persona as well as the denied persona."),
            ]
            for incident in self.store.incidents():
                overlap = sorted(set(incident["components"]) & set(analysis["components"]))
                if overlap and incident["reviewed"]:
                    matched = {**incident, "matched_components": overlap, "match_reason": "Shared components: " + ", ".join(overlap)}
                    analysis["incidents"].append(matched)
                    kind = incident["regression_kind"]
                    dependencies = ["permissions"] if kind == "permission" else ["routing"]
                    analysis["checks"].append(make_check("REG-" + incident["id"], "Regression: " + incident["title"], kind,
                        incident["actor"], dependencies + common, incident["id"], matched["match_reason"]))
            analysis["snapshot"] = snapshot(config, target, analysis["requirements"])
        else:
            live = self.adapter.collect(work_item)
            story = live["story"]
            criteria = story.get("acceptanceCriteria", story.get("acceptance_criteria", []))
            if isinstance(criteria, str):
                criteria = [line.strip() for line in criteria.splitlines() if line.strip()]
            if not isinstance(criteria, list):
                criteria = []
            texts = [c if isinstance(c, str) else str(c.get("text", "")) for c in criteria if isinstance(c, (str, dict))]
            texts = [t for t in texts if t] or ["Acceptance criteria unavailable; configure the work-item mapping."]
            analysis.update(title=str(story.get("title", story.get("Name", work_item))), config={}, components=[],
                requirements="\n".join(texts), baseline=[], runner="Agentia CLI", raw_evidence=live,
                warnings=live["warnings"], limitations=["Live output schemas require validation against your installed CLI.",
                "Business test assertions, personas, and target metadata are not yet bound to claims."])
            analysis["checks"] = [make_check(f"AC-{i+1}", text, "unmapped", "Unmapped", ["requirements", "environment"], "story", "Requires a reviewed test assertion mapping.") for i, text in enumerate(texts)]
            analysis["snapshot"] = {"revision": live["revision"], "environment": target, "complete": False,
                                    "parts": {"requirements": digest(texts), "environment": digest([target, "unobserved"])}, "observed_at_source": "Agentia story; target freshness unknown"}
        analysis["events"].append({"at": now(), "action": "analysis_created", "detail": "Verification obligations recorded; no passing claims assumed."})
        return self.store.save(evaluate(analysis))

    def get(self, analysis_id, version=None):
        return self.store.get(identifier(analysis_id), version)

    def mutate(self, analysis_id, payload):
        with self.lock:
            analysis = self.get(analysis_id)
            self._assert_editable(analysis, payload.get("expected_version"))
            if analysis["mode"] != "demo":
                raise ValueError("Scenario controls apply only to the local demo model.")
            action = payload.get("action")
            config = analysis["config"]
            if action == "fix_boundary":
                config["inclusive"] = False
            elif action == "introduce_boundary_bug":
                config["inclusive"] = True
            elif action == "revoke_permission":
                config["permission"] = False
            elif action == "restore_permission":
                config["permission"] = True
            elif action == "unrelated_change":
                config["notes_revision"] += 1
            elif action == "change_environment":
                analysis["environment"] = environment(payload.get("environment"))
            else:
                raise ValueError("Unknown scenario change")
            analysis["snapshot"] = snapshot(config, analysis["environment"], analysis["requirements"])
            analysis["baseline"] = baseline(config)
            analysis["updated_at"] = now()
            analysis["events"].append({"at": now(), "action": action, "detail": "Recomputed input fingerprints and dependent evidence freshness."})
            return self.store.save(evaluate(analysis), expected_version=payload["expected_version"])

    def _assert_editable(self, analysis, version):
        if type(version) is not int or version != analysis["version"]:
            raise ValueError("Analysis changed. Refresh before retrying.")
        if self.store.active(analysis["id"]):
            raise ValueError("A check run is already active for this analysis.")

    def start_run(self, analysis_id, expected_version, background=True):
        with self.lock:
            analysis = self.get(analysis_id)
            self._assert_editable(analysis, expected_version)
            selected = [c["id"] for c in analysis["checks"] if c["status"] != "passed"]
            if not selected and analysis["mode"] == "demo":
                raise ValueError("All checks are current; no recheck is needed.")
            job = {"id": "RUN-" + uuid.uuid4().hex[:12].upper(), "analysis_id": analysis_id, "analysis_version": expected_version,
                   "status": "queued", "selected": selected, "created_at": now(), "detail": "Waiting for execution"}
            try:
                self.store.put_job(job)
            except sqlite3.IntegrityError as exc:
                raise ValueError("Another run is active for this analysis.") from exc
        if background:
            threading.Thread(target=self._execute, args=(job, analysis), daemon=True).start()
        else:
            self._execute(job, analysis)
        return self.store.job(job["id"])

    def _execute(self, job, analysis):
        job.update(status="running", detail="Executing selected checks", started_at=now())
        self.store.put_job(job)
        try:
            if analysis["mode"] == "live":
                analysis["live_results"] = self.adapter.run_live(analysis["work_item_id"])
            else:
                for check in analysis["checks"]:
                    if check["id"] not in job["selected"]:
                        continue
                    hashes = {key: analysis["snapshot"]["parts"][key] for key in check["dependencies"]}
                    result = {"run_id": job["id"], "at": now(), "revision": analysis["snapshot"]["revision"],
                              "environment": analysis["environment"], "runner": analysis["runner"], "input_hashes": hashes}
                    try:
                        if analysis["config"]["scenario"] == "unavailable":
                            raise ValueError("Seeded runner outage; no execution evidence is available.")
                        result.update(execute(check, analysis["config"]))
                        result["status"] = "passed" if result["actual"] == result["expected"] else "failed"
                        result["log"] = f"{check['id']} | {result['input']} | expected={result['expected']} | actual={result['actual']} | {result['status'].upper()}"
                    except ValueError as exc:
                        result.update(status="unverified", input="unavailable", expected="Execution evidence", actual="Not obtained", log=str(exc))
                    result["artifact_digest"] = digest(result)
                    check.update(status=result["status"], result=result, stale_reason=None)
            analysis["runs"].append({"id": job["id"], "selected": job["selected"], "at": now(), "runner": analysis["runner"]})
            analysis["events"].append({"at": now(), "action": "checks_completed", "detail": f"Executed {len(job['selected'])} selected check(s); evaluated {POLICY}."})
            analysis["updated_at"] = now()
            self.store.save(evaluate(analysis), expected_version=job["analysis_version"])
            job.update(status="completed", detail="Results persisted", completed_at=now())
        except Exception as exc:
            job.update(status="failed", detail=str(exc) if isinstance(exc, ValueError) else "Execution failed. No claims were marked passed.", completed_at=now())
        self.store.put_job(job)

    def import_incident(self, payload):
        iid = identifier(payload.get("id"), "incident ID")
        if iid == SEED_INCIDENT["id"]:
            raise ValueError("The bundled synthetic incident is reserved. Use a new incident ID.")
        components = payload.get("components")
        if not isinstance(components, list) or not 1 <= len(components) <= 50 or any(not isinstance(c, str) or not 1 <= len(c) <= 200 for c in components):
            raise ValueError("Provide 1–50 component names")
        for field in ("title", "root_cause", "actor", "provenance"):
            if not isinstance(payload.get(field), str) or not 1 <= len(payload[field]) <= 2000:
                raise ValueError(f"Provide a valid {field}")
        if payload.get("regression_kind") not in {"permission", "boundary", "high", "low"}:
            raise ValueError("Supported local regression kinds: permission, boundary, high, low")
        if type(payload.get("reviewed")) is not bool:
            raise ValueError("Set reviewed explicitly to true or false")
        incident = {k: payload[k] for k in ("id", "title", "components", "root_cause", "actor", "provenance", "regression_kind", "reviewed")}
        incident["synthetic"] = True
        incident["scope"] = "Local model; no live test mapping"
        return self.store.put_incident(incident)

    def bundle(self, analysis_id, version=None):
        data = self.get(analysis_id, version)
        return {"format": "releaseproof-evidence-v1", "analysis": data, "sha256": digest(data),
                "integrity_note": "Unsigned content digest; identity is checked against this local store. Not a deployment authorization."}

    def verify(self, bundle):
        data = bundle.get("analysis")
        if bundle.get("format") != "releaseproof-evidence-v1" or not isinstance(data, dict):
            raise ValueError("Unsupported evidence bundle")
        integrity = digest(data) == bundle.get("sha256")
        trusted, fresh = False, False
        stale_checks = []
        try:
            original = self.get(data["id"], data["version"])
            trusted = digest(original) == digest(data)
            current = self.get(data["id"])
            inspected = copy.deepcopy(data)
            inspected["snapshot"] = current["snapshot"]
            evaluate(inspected)
            stale_checks = [c["id"] for c in inspected["checks"] if c["status"] == "stale"]
            fresh = trusted and current["mode"] == "demo" and not stale_checks and bool(data["checks"]) and all(c.get("result") for c in data["checks"])
        except (KeyError, ValueError, TypeError):
            pass
        return {"integrity": integrity, "matches_local_record": trusted, "freshness": "current" if fresh else "stale" if stale_checks else "unknown",
                "stale_checks": stale_checks, "valid": integrity and trusted and fresh,
                "detail": "Freshness compares the latest local analysis snapshot. This is not a live org observation, signature, safety guarantee, or approval."}

    def compare(self, analysis_id, older):
        previous, current = self.get(analysis_id, older), self.get(analysis_id)
        old_checks = {c["id"]: c for c in previous["checks"]}
        return {"from_version": previous["version"], "to_version": current["version"],
                "from_decision": previous["decision"]["state"], "to_decision": current["decision"]["state"],
                "changes": [{"id": c["id"], "title": c["title"], "before": old_checks.get(c["id"], {}).get("status", "absent"), "after": c["status"]}
                            for c in current["checks"] if old_checks.get(c["id"], {}).get("status") != c["status"]]}
