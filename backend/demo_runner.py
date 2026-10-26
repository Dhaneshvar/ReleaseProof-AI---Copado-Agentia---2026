"""Executable LOCAL reference model. This does not execute Apex or call Salesforce.

The requirement oracle is independent of the intentionally defective implementation.
Scenario changes select model inputs; no arbitrary code supplied by clients is run.
"""
from __future__ import annotations

import hashlib
import json

MODEL_VERSION = "lead-model-1"
TEST_VERSION = "lead-contract-checks-1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def route_lead(score, threshold, inclusive):
    qualifies = score >= threshold if inclusive else score > threshold
    return "Senior Sales" if qualifies else "Standard Sales"


def override_route(actor):
    return "allowed" if actor == "Sales Manager" else "denied"


def standard_user_route(has_permission):
    return "allowed" if has_permission else "denied"


def snapshot(config, environment, requirement_text):
    parts = {
        "routing": digest([MODEL_VERSION, config["inclusive"], config["threshold"]]),
        "authorization": digest([MODEL_VERSION, "manager-only-override"]),
        "permissions": digest(config["permission"]),
        "requirements": digest(requirement_text),
        "tests": digest(TEST_VERSION),
        "environment": digest(["local-simulation", environment]),
        "policy": digest("all-required-checks-current-v1"),
    }
    return {"revision": digest([parts, config.get("notes_revision", 0)])[:12], "parts": parts,
            "environment": environment, "observed_at_source": "local reference model", "complete": True}


def baseline(config):
    cases = []
    for score, expected in [(config["threshold"] - 20, "Standard Sales"), (config["threshold"] + 20, "Senior Sales")]:
        actual = route_lead(score, config["threshold"], config["inclusive"])
        cases.append({"input": f"score = {score}", "expected": expected, "actual": actual, "status": "passed" if actual == expected else "failed"})
    return cases


def execute(check, config):
    kind = check["kind"]
    if kind in {"boundary", "high", "low"}:
        offset = {"boundary": 0, "high": 1, "low": -1}[kind]
        score = config["threshold"] + offset
        expected = "Senior Sales" if offset > 0 else "Standard Sales"
        return {"input": f"score = {score}", "expected": expected,
                "actual": route_lead(score, config["threshold"], config["inclusive"])}
    if kind == "override":
        return {"input": f"actor = {check['actor']}", "expected": "allowed" if check["actor"] == "Sales Manager" else "denied",
                "actual": override_route(check["actor"])}
    if kind == "permission":
        return {"input": "Standard Sales user opens Lead routing", "expected": "allowed", "actual": standard_user_route(config["permission"])}
    raise ValueError("No executable mapping for this check")
