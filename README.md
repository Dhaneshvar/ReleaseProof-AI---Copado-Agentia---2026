# ReleaseProof AI

A versioned evidence ledger for Salesforce release requirements, built with Next.js/React and a shared Python engine.

## What is implemented

- Deterministic decision policy: failed checks block; changed inputs make evidence stale; missing evidence stays unverified.
- Executable **local reference-model** scenarios: a strict score boundary, allowed/denied override personas, missing permissions, incident matching, and runner outage.
- Independent requirement assertions expose a seeded boundary defect even when the baseline examples pass.
- Structured incident import; reviewed matching incidents create regression obligations.
- Selective invalidation across routing, authorization, permissions, requirements, test version, environment and policy fingerprints.
- SQLite persistence, immutable analysis versions, decision comparison, execution timeline and asynchronous jobs.
- Evidence exports and a verifier checking digests, the trusted local original, and latest local fingerprints.
- A headless CLI using the same service as both API transports.
- An explicit live Agentia adapter for story/dependency reads, connection probes, local gates and CRT execution/polling.
- Responsive evidence UI, search/filter, native keyboard-accessible detail dialogs, and PWA shell caching. APIs are never cached by the service worker.

## Important boundaries

The local runner executes Python functions. It does **not** execute Apex, connect to Salesforce, or run CRT. Its synthetic results are labeled throughout the app and exported bundles.

The live adapter has been tested against controlled responses, but has not been validated against an authenticated Copado account. Copado access was not available during implementation. It fails explicitly rather than returning demo evidence.

Live business-assertion mappings, target metadata snapshots, a real persona test setup, and LLM requirement interpretation are not implemented. Generic live test success does not mark business requirements verified. The connection page reports these limitations. No promotion, deployment, auto-remediation, user-authentication system, or production approval action is implemented.

## Run locally on Windows

From this project directory:

```powershell
python server.py
```

In a second terminal:

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:3000. The API binds only to 127.0.0.1:8000. SQLite data lives in `data/releaseproof.sqlite3`, which is excluded from Git. Configure `RELEASEPROOF_DB` for another location, or `RELEASEPROOF_PORT` for a different API port.

The server reads process environment variables. It does not automatically load the root `.env.example`. Set variables in the launching PowerShell session or your process manager. The Next.js proxy accepts `RELEASEPROOF_BACKEND_URL` (default http://127.0.0.1:8000).

Optional FastAPI transport:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Run only one backend process against the database at a time. Startup marks unfinished local jobs interrupted; a remote job may still be running and must be inspected before retrying.

Production-shaped web preview:

```powershell
cd web
npm run build
npm start
```

This is a single-user local prototype. Do not expose it publicly without authentication, authorization, secure deployment configuration, and appropriate data access controls.

## Five-minute local demonstration

1. Select **Missed boundary**, work item US-247, threshold 80, and Analyze.
2. The baseline examples pass but the decision remains incomplete.
3. Click **Run required checks**. AC-2 fails: score 80 expects Standard Sales but observes Senior Sales. Open the counterexample for the recorded assertion.
4. Click **Apply boundary fix**. Two routing checks become stale. Authorization and permission evidence stays current.
5. Click **Run required checks**. The two selected checks pass. The modeled evidence requirements are satisfied; approval is still separate.
6. Export the bundle.
7. Click **Remove permission**. Only the incident-derived regression becomes stale.
8. Open History and verify the old bundle: its digest and stored original match, but the permission check is stale.
9. Run required checks; the missing permission is now a reproduced failure. Restore permission and recheck to recover.
10. Try **Edit unrelated notes**: independent evidence remains current.

Additional scenarios: correct implementation, missing permission, unrelated-to-incident change, and unavailable runner. Change the threshold to exercise different boundary values. Changing the modeled target invalidates all environment-bound checks.

## Headless workflow

All commands return JSON. Replace the sample analysis ID with one returned by analyze.

```powershell
python releaseproof.py analyze US-247 --environment UAT --mode demo --scenario boundary_bug --json
python releaseproof.py run-checks RP-RETURNED-ID --json
python releaseproof.py explain RP-RETURNED-ID AC-2 --json
python releaseproof.py change RP-RETURNED-ID fix_boundary --json
python releaseproof.py run-checks RP-RETURNED-ID --json
python releaseproof.py export RP-RETURNED-ID --output evidence.json
python releaseproof.py verify evidence.json --json
python releaseproof.py connections --json
```

Exit codes: 0 for a successful command; 1 for a command/input error; 2 for a completed check run with unresolved evidence, or an invalid/stale/unknown bundle verification. Export uses exclusive creation and will not overwrite an existing file. A valid evidence bundle may contain failed results; bundle validity is not release readiness.

## Copado setup when access is available

Follow the current [Agentia documentation](https://developer.copado.com/docs) and [workflow guide](https://developer.copado.com/guides). Install and authenticate locally; never paste credentials into ReleaseProof.

```powershell
npm install -g @copado/agentia-cli@beta
agentia setup
$env:RELEASEPROOF_SALESFORCE_REPO = 'D:\\path\\to\\salesforce-checkout'
$env:COPADO_PIPELINE_ID = 'pipeline-id'
$env:COPADO_SOURCE_ORG_ID = 'source-org-id'
$env:COPADO_SOURCE_CREDENTIAL_ID = 'source-credential-id'
$env:COPADO_CRT_PROJECT_ID = 'crt-project-id'
$env:COPADO_CRT_JOB_ID = 'crt-job-id'
python server.py
```

Use a Copado Source Format project. Set `AGENTIA_BIN` if the CLI is not on PATH. `COPADO_BASE_REF` defaults to origin/main. Set your active Agentia story from the Salesforce checkout yourself; ReleaseProof checks its identity before executing local gates.

Open **Connections → Check connections**. A backend health response is not authentication. CRT checks use its separate readiness response. Only after CI/CD is confirmed does the UI enable live analysis.

The adapter collects a work item and configured dependency information. Running checks can execute the project's local quality gate script and start the explicitly configured CRT job; it does not promote or deploy. Supported result envelopes are `result`, `data`, or a top-level object. Unknown statuses remain unverified. The adapter records CRT build IDs and bounded polling results. It does not currently download remote logs/artifacts or bind test assertions to business claims.

Validate the installed CLI's output schemas and target/branch setup before trusting an integration. Record the tested CLI version once available. No compatible version is claimed until that validation happens.

## Incident JSON

Import from History or `python releaseproof.py import-incident incident.json`. Records persist and affect new analyses, keeping existing analysis versions unchanged.

```json
{
  "id": "INC-2048",
  "title": "Routing threshold equality",
  "components": ["LeadScoreRouter.model"],
  "root_cause": "Equality was included in a strict greater-than condition.",
  "regression_kind": "boundary",
  "actor": "Routing service",
  "reviewed": true,
  "provenance": "Synthetic regression example"
}
```

Supported local kinds: permission, boundary, high, low. Imported records are explicitly scoped to the local reference model. Unreviewed incidents do not create required checks. INC-1042 is a reserved synthetic seed. Matching uses exact component overlap, not invented failure probabilities.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/health | Backend availability and version |
| GET / POST | /api/capabilities | Configuration / explicit read-only connection probes |
| POST | /api/analyze | Create an explicit demo or live analysis |
| GET | /api/analyses | Latest saved analyses |
| GET | /api/analyses/{id} | Analysis and active run |
| POST | /api/analyses/{id}/run | Execute selected checks; requires expected_version |
| POST | /api/analyses/{id}/change | Change demo inputs; requires expected_version and action |
| GET | /api/analyses/{id}/history | Immutable versions |
| GET | /api/analyses/{id}/compare?version=1 | Compare with latest |
| GET | /api/analyses/{id}/bundle | Downloadable evidence object |
| GET | /api/jobs/{id} | Persisted execution status |
| GET / POST | /api/incidents | List/import structured incidents |
| POST | /api/verify | Verify an evidence bundle against local records |

## Verification

```powershell
python -m unittest discover -s tests -v
cd web
node node_modules/typescript/bin/tsc --noEmit
npm run build
```

The backend tests cover the boundary counterexample, corrective rechecks, persona permission failure, history relevance, source/environment freshness, unrelated-change control, outage behavior, changed threshold values, persisted versions, incident import, conflicting updates, interrupted jobs, live failures, conservative status parsing, and bundle tampering.

Test outcomes establish behavior on synthetic fixtures, not general Salesforce defect-detection accuracy.

## Evidence and offline behavior

Snapshots bind known inputs. The demo dependency model is explicit and limited; live target snapshots are unavailable and never reported current. Verification compares the latest local snapshot, not a continuously monitored Salesforce org.

Bundles contain unsigned SHA-256 digests and are compared with the stored original. This catches altered exports relative to that local trust anchor. It is not issuer authentication, a compliance certificate, or formal proof.

The PWA caches only its shell/static resources. Its locally saved last analysis is visibly marked as an offline copy when the API cannot be reached; freshness is unknown and evidence actions are disabled.

See [HACKATHON_STRATEGY.md](HACKATHON_STRATEGY.md) for the research and longer-term plan.

