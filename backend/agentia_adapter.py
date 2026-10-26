"""Bounded Agentia integration. Unknown responses never become passing evidence."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


def unwrap(payload):
    return payload.get("result", payload.get("data", payload)) if isinstance(payload, dict) else payload


def outcome(payload):
    data = unwrap(payload)
    status = str(data.get("status", "")).lower() if isinstance(data, dict) else ""
    if status in {"passed", "pass", "success", "succeeded"}:
        return "passed"
    if status in {"failed", "fail", "error", "aborted", "cancelled"}:
        return "failed"
    return "unverified"


def public_data(value):
    if isinstance(value, dict):
        return {k: public_data(v) for k, v in value.items()
                if not re.search(r"token|secret|password|credential|authorization|api.?key|pak", k, re.I)}
    if isinstance(value, list):
        return [public_data(v) for v in value]
    return value


class AgentiaAdapter:
    def __init__(self):
        self.executable = shutil.which(os.getenv("AGENTIA_BIN", "agentia"))
        self.repo = os.getenv("RELEASEPROOF_SALESFORCE_REPO", "")

    def call(self, *args, timeout=45):
        if not self.executable:
            raise ValueError("Agentia CLI is missing. Install it and configure Agentia locally.")
        if not self.repo or not Path(self.repo).is_dir():
            raise ValueError("Set RELEASEPROOF_SALESFORCE_REPO to your Copado Salesforce checkout.")
        # npm launchers can be .cmd files on Windows. Reject shell metacharacters.
        if any(re.search(r'[&|<>^%\r\n"\x60]', str(arg)) for arg in args):
            raise ValueError("Unsupported characters in Agentia arguments")
        try:
            proc = subprocess.run([self.executable, *args, "--json"], cwd=self.repo,
                                  capture_output=True, text=True, timeout=timeout, shell=False)
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Agentia timed out. Evidence remains unverified.") from exc
        if proc.returncode:
            # stderr may contain credentials. Keep it out of API responses.
            raise ValueError(f"Agentia {' '.join(args[:3])} failed (exit {proc.returncode}). Inspect the CLI locally.")
        try:
            data = json.loads(proc.stdout)
        except ValueError as exc:
            raise ValueError("Unsupported Agentia response: expected JSON.") from exc
        if isinstance(data, dict) and (data.get("success") is False or data.get("error")):
            raise ValueError("Agentia reported an error; inspect the CLI locally.")
        return data

    def capabilities(self, probe=False):
        result = {
            "backend": "available", "cli": "available" if self.executable else "missing",
            "repository": "configured" if self.repo and Path(self.repo).is_dir() else "missing",
            "cicd": "unchecked", "crt": "unchecked", "ai": "not_integrated", "live_ready": False,
            "detail": "Check connections to run read-only Agentia probes.",
            "required_configuration": [n for n in ["RELEASEPROOF_SALESFORCE_REPO", "COPADO_PIPELINE_ID",
                "COPADO_SOURCE_ORG_ID", "COPADO_SOURCE_CREDENTIAL_ID", "COPADO_CRT_PROJECT_ID", "COPADO_CRT_JOB_ID"] if not os.getenv(n)],
        }
        if not self.executable:
            result.update(cicd="unavailable", crt="unavailable", detail="Agentia CLI is missing. Live Copado execution is unavailable.")
        elif probe:
            try:
                self.call("cicd", "work", "list", "--assigned-to-me", timeout=15)
                result["cicd"] = "connected"
            except ValueError as exc:
                result.update(cicd="unavailable", detail=str(exc))
            try:
                auth = unwrap(self.call("auth", "get", "--crt", timeout=15))
                result["crt"] = "ready" if isinstance(auth, dict) and auth.get("ready") is True else "not_ready"
            except ValueError:
                result["crt"] = "unavailable"
            result["live_ready"] = result["cicd"] == "connected"
        return result

    def collect(self, work_item):
        story = unwrap(self.call("cicd", "work", "get", work_item))
        if not isinstance(story, dict):
            raise ValueError("Unsupported work-item schema. No business claims were inferred.")
        dependencies, warnings = [], []
        names = ["COPADO_PIPELINE_ID", "COPADO_SOURCE_ORG_ID", "COPADO_SOURCE_CREDENTIAL_ID"]
        if all(os.getenv(n) for n in names):
            try:
                deps = unwrap(self.call("cicd", "metadata", "dependency", "list", "--from-changes",
                    "--base-ref", os.getenv("COPADO_BASE_REF", "origin/main"), "--pipeline-id", os.environ[names[0]],
                    "--source-org-id", os.environ[names[1]], "--source-credential-id", os.environ[names[2]]))
                dependencies = public_data(deps if isinstance(deps, list) else deps.get("dependencies", [])) if isinstance(deps, (list, dict)) else []
            except ValueError as exc:
                warnings.append(str(exc))
        else:
            warnings.append("Metadata dependency configuration is missing.")
        try:
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo,
                capture_output=True, text=True, timeout=10, check=True).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            revision = "unknown"
        return {"story": public_data(story), "dependencies": dependencies, "revision": revision, "warnings": warnings}

    def run_live(self, work_item):
        """Supplementary runner results cannot certify business claims without mappings."""
        active = unwrap(self.call("cicd", "work", "get"))
        identifiers = [str(active.get(k, "")) for k in ("id", "name", "Name", "workItemId")] if isinstance(active, dict) else []
        if work_item not in identifiers:
            raise ValueError("Active Agentia work item differs from this analysis. Bind it in the Salesforce checkout before executing.")
        results = []
        try:
            gate = self.call("cicd", "work", "test", "--local", timeout=180)
            results.append({"name": "Agentia local quality gates", "status": outcome(gate), "artifact": public_data(gate)})
        except ValueError as exc:
            results.append({"name": "Agentia local quality gates", "status": "unverified", "detail": str(exc)})
        project, job = os.getenv("COPADO_CRT_PROJECT_ID"), os.getenv("COPADO_CRT_JOB_ID")
        if not project or not job:
            results.append({"name": "Copado Robotic Testing", "status": "unverified", "detail": "Configure CRT project and job IDs."})
            return results
        try:
            auth = unwrap(self.call("auth", "get", "--crt"))
            if not isinstance(auth, dict) or auth.get("ready") is not True:
                raise ValueError("CRT credentials are not ready.")
            started = unwrap(self.call("testing", "build", "run", job, "--project", project))
            build_id = started.get("id", started.get("buildId")) if isinstance(started, dict) else None
            if not isinstance(build_id, (str, int)):
                raise ValueError("No supported CRT build ID was returned. Inspect remote runs before retrying.")
            final, deadline = started, time.monotonic() + 150
            while outcome(final) == "unverified" and time.monotonic() < deadline:
                time.sleep(2)
                final = self.call("testing", "build", "get", str(build_id), "--project", project, "--job", job, "--full")
            results.append({"name": "Copado Robotic Testing", "status": outcome(final),
                            "build_id": str(build_id), "artifact": public_data(final),
                            "detail": "Review remote artifacts; business claim and environment mappings are still required."})
        except ValueError as exc:
            results.append({"name": "Copado Robotic Testing", "status": "unverified", "detail": str(exc)})
        return results

