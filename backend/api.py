"""A shared API contract for FastAPI and the zero-dependency local server."""
from urllib.parse import parse_qs, urlsplit

from .engine import SCENARIOS, ReleaseService


def summary(item):
    return {k: item[k] for k in ("id", "version", "work_item_id", "title", "environment", "mode", "updated_at", "decision", "summary")}


def dispatch(service: ReleaseService, method, path, body=None):
    body = body or {}
    parsed = urlsplit(path)
    parts = parsed.path.strip("/").split("/")
    query = parse_qs(parsed.query)
    if method == "GET" and parts == ["api", "health"]:
        return {"status": "ok", "service": "releaseproof-api", "version": "0.3.0"}
    if parts == ["api", "capabilities"] and method in {"GET", "POST"}:
        return service.adapter.capabilities(probe=method == "POST")
    if method == "GET" and parts == ["api", "scenarios"]:
        return {"scenarios": [{"id": key, "label": item["label"]} for key, item in SCENARIOS.items()]}
    if method == "POST" and parts == ["api", "analyze"]:
        return service.analyze(body)
    if method == "GET" and parts == ["api", "analyses"]:
        return {"analyses": [summary(a) for a in service.store.list()]}
    if len(parts) >= 3 and parts[:2] == ["api", "analyses"]:
        aid = parts[2]
        if len(parts) == 3 and method == "GET":
            return {**service.get(aid), "active_run": service.store.active(aid)}
        if len(parts) == 4:
            action = parts[3]
            if method == "POST" and action == "run":
                return service.start_run(aid, body.get("expected_version"))
            if method == "POST" and action == "change":
                return service.mutate(aid, body)
            if method == "GET" and action == "history":
                service.get(aid)
                return {"versions": [summary(a) for a in service.store.history(aid)]}
            version = int(query["version"][0]) if "version" in query else None
            if method == "GET" and action == "bundle":
                return service.bundle(aid, version)
            if method == "GET" and action == "compare":
                return service.compare(aid, version or 1)
    if method == "GET" and len(parts) == 3 and parts[:2] == ["api", "jobs"]:
        return service.store.job(parts[2])
    if parts == ["api", "incidents"]:
        if method == "GET":
            return {"incidents": service.store.incidents()}
        if method == "POST":
            return service.import_incident(body)
    if method == "POST" and parts == ["api", "verify"]:
        return service.verify(body)
    raise KeyError("Endpoint not found")
