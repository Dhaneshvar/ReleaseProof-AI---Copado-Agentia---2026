# ReleaseProof AI — deadline checklist

Use this checklist on October 26, 2026. The demo mode is ready without Copado access. Live Agentia access requires the Copado account and project setup described below.

## 1. Start the demo

From the repository root:

```powershell
python server.py
```

In another terminal:

```powershell
cd web
node node_modules/next/dist/bin/next dev -p 3000
```

Open <http://localhost:3000/>.

If the first page request takes time, wait for the Next.js compilation to finish once, then refresh.

## 2. Run the winning demo path

1. Choose `LOCAL DEMO`.
2. Use work item `US-247`, target `UAT`, scenario `Missed boundary`, threshold `80`.
3. Select **Analyze**.
4. Select **Run required checks**.
5. Open the counterexample. It shows:

   - expected: `Standard Sales`
   - observed: `Senior Sales`
   - input: `score = 80`
   - decision: `Release blocked`

6. Select **Apply boundary fix**.
7. Run the two stale routing checks again. The decision becomes `Evidence requirements satisfied`.
8. Select **Remove permission**. Only the incident-derived standard-user regression becomes stale.
9. Run the regression. It fails and blocks the decision again.
10. Open **History**, compare versions, and export the evidence bundle.

This demonstrates the project’s central behavior: evidence is executable, historical memory changes the test plan, and evidence becomes stale when its assumptions change.

## 3. Verify from the terminal

```powershell
python -m unittest discover -s tests -v
python -m compileall -q backend server.py releaseproof.py
cd web
node node_modules/typescript/bin/tsc --noEmit
```

The backend test suite should report 18 passing tests.

## 4. Try Agentia live setup

Run these commands in a normal user terminal. Do not put credentials in `.env`, source code, chat, or the public repository.

```powershell
npm install -g @copado/agentia-cli@beta
agentia setup
agentia auth get --json
agentia cicd work list --assigned-to-me --json
```

If npm does not return, retry from a terminal with a network connection:

```powershell
npm config get registry
npm install -g @copado/agentia-cli@beta --registry=https://registry.npmjs.org
```

Then configure the current PowerShell session. Replace only the identifiers with values from your Copado project:

```powershell
$env:RELEASEPROOF_SALESFORCE_REPO = 'D:\path\to\copado-salesforce-checkout'
$env:COPADO_PIPELINE_ID = 'pipeline-id'
$env:COPADO_SOURCE_ORG_ID = 'source-org-id'
$env:COPADO_SOURCE_CREDENTIAL_ID = 'source-credential-id'
$env:COPADO_CRT_PROJECT_ID = 'crt-project-id'
$env:COPADO_CRT_JOB_ID = 'crt-job-id'
```

The checkout must be the repository linked to the Copado Source Format pipeline. Set the active Agentia story from that checkout, then open **Connections → Check connections** in ReleaseProof. The UI must show separate CI/CD and CRT states. A generic health response is not proof of authentication.

## 5. Five-minute recording script

**0:00–0:30** — State the requirement: scores greater than 80 route to Senior Sales; score 80 stays Standard Sales.

**0:30–1:00** — Show the existing example suite passing. Explain that it skips the equality boundary and persona permission check.

**1:00–2:00** — Run ReleaseProof. Show the score-80 counterexample and `Release blocked` decision.

**2:00–2:40** — Open INC-1042. Explain that the previous permission failure adds a required standard-user regression.

**2:40–3:30** — Apply the reviewed boundary fix and rerun only the two dependent checks.

**3:30–4:10** — Remove the modeled permission. Show the old evidence becoming stale and the incident regression failing.

**4:10–4:40** — Export and verify the versioned evidence bundle. Show the revision, environment, run ID, assertion, and artifact digest.

**4:40–5:00** — State the limitation honestly: demo mode uses a deterministic local reference model; live mode is wired to Agentia and remains disabled until the Copado account and project are configured.

Do not show credentials, private customer data, or an unverified live result. The recording must match the behavior in the public repository.

## 6. Submission files

- Public GitHub repository containing the source.
- Demo video of five minutes or less.
- Slide deck in English.
- Short description using the title: **ReleaseProof AI — Evidence-driven release intelligence powered by Agentia**.

Use this description:

> ReleaseProof AI converts Salesforce business requirements into executable verification obligations. It runs targeted checks, exposes counterexamples that a green baseline suite can miss, turns reviewed incidents into required regression checks, and invalidates evidence when its code, permission, target, or policy assumptions change. Agentia remains the controlled execution layer; ReleaseProof explains which business promises are verified and what still needs a human decision.

The official rules require a publicly accessible repository, a presentation deck, and a demo video of up to five minutes. Submit before the published October 26 deadline.
