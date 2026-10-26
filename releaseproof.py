"""Headless entry point: python releaseproof.py --help."""
import argparse
import json
import sys
from pathlib import Path

from backend.engine import ReleaseService


def main(argv=None):
    parser = argparse.ArgumentParser(description="ReleaseProof evidence engine. Demo runs a local model; live uses configured Agentia.")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze")
    analyze.add_argument("work_item_id")
    analyze.add_argument("--environment", default="UAT", choices=["DEV", "QA", "UAT", "PROD"])
    analyze.add_argument("--mode", default="demo", choices=["demo", "live"])
    analyze.add_argument("--scenario", default="boundary_bug")
    analyze.add_argument("--threshold", type=int, default=80)
    run = sub.add_parser("run-checks")
    run.add_argument("analysis_id")
    show = sub.add_parser("show")
    show.add_argument("analysis_id")
    export = sub.add_parser("export")
    export.add_argument("analysis_id")
    export.add_argument("--output", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("bundle")
    explain = sub.add_parser("explain")
    explain.add_argument("analysis_id")
    explain.add_argument("claim_id")
    change = sub.add_parser("change")
    change.add_argument("analysis_id")
    change.add_argument("action", choices=["fix_boundary", "introduce_boundary_bug", "revoke_permission", "restore_permission", "unrelated_change"])
    imported = sub.add_parser("import-incident")
    imported.add_argument("file")
    sub.add_parser("connections")
    for item in sub.choices.values():
        item.add_argument("--json", action="store_true", help="Structured JSON (also the default)")
    args = parser.parse_args(argv)
    service = ReleaseService()
    try:
        if args.command == "analyze":
            result = service.analyze(vars(args))
        elif args.command == "run-checks":
            analysis = service.get(args.analysis_id)
            job = service.start_run(args.analysis_id, analysis["version"], background=False)
            result = {"job": job, "analysis": service.get(args.analysis_id)}
        elif args.command == "show":
            result = service.get(args.analysis_id)
        elif args.command == "export":
            result = service.bundle(args.analysis_id)
            # Exclusive creation avoids overwriting an existing evidence bundle.
            with Path(args.output).open("x", encoding="utf-8") as output:
                json.dump(result, output, indent=2)
            result = {"output": str(Path(args.output).resolve()), "sha256": result["sha256"]}
        elif args.command == "verify":
            result = service.verify(json.loads(Path(args.bundle).read_text(encoding="utf-8")))
        elif args.command == "explain":
            analysis = service.get(args.analysis_id)
            result = next((c for c in analysis["checks"] if c["id"] == args.claim_id), None)
            if result is None:
                raise ValueError("Claim not found")
        elif args.command == "change":
            analysis = service.get(args.analysis_id)
            result = service.mutate(args.analysis_id, {"action": args.action, "expected_version": analysis["version"]})
        elif args.command == "import-incident":
            result = service.import_incident(json.loads(Path(args.file).read_text(encoding="utf-8")))
        else:
            result = service.adapter.capabilities(probe=True)
        print(json.dumps(result, indent=2))
        if args.command == "verify" and not result["valid"]:
            return 2
        if args.command == "run-checks" and (result["job"]["status"] != "completed" or result["analysis"]["decision"]["state"] != "satisfied"):
            return 2
        return 0
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
