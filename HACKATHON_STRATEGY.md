# ReleaseProof AI — hackathon research and build strategy

Research date: October 12, 2026. This document proposes future work; it does not mark those capabilities as implemented. It combines inspection of the current repository with public product documentation. Novelty assessments are judgments about the reviewed material, not claims of worldwide invention or an exhaustive competitive audit.

Implementation update: the shared decision engine, executable local-model scenarios, incident persistence/import, selective invalidation, versioned evidence bundles, asynchronous local jobs, headless CLI, and updated UI are now implemented. The README documents their scope. Live account validation, actual Salesforce/Apex/persona execution, assertion mappings, target snapshots, and LLM interpretation remain outstanding. The research findings below describe the code at the time of the original audit.

## Recommended position

**ReleaseProof AI turns a Salesforce business requirement into an executable release contract, challenges it with targeted tests, and keeps its evidence valid as the release changes. Powered by Copado Agentia.**

The buyer/user is a release owner who must answer: “For this change, in this environment, for these users, what behavior have we actually checked—and what is still unknown?”

The distinctive workflow should be:

`Requirement → verification obligations → counterexample → Agentia test execution → evidence-backed decision → selective revalidation after change`

Historical incidents contribute new obligations to that same workflow. The graph supplies the traceability and invalidation paths. The dashboard makes the reasoning inspectable. Neither needs to become a separate product.

“Proof” means evidence for stated requirements under recorded conditions. It is not mathematical proof of all possible behavior, a guarantee of a safe release, or a compliance certification.

## Verified event requirements and strategy

The rendered official rules, amended October 9, list registration through October 19 and submission by October 26, 2026. They require a public GitHub repository, presentation deck, and original demo video of no more than five minutes. Entries are individual. Each of five criteria earns 1–10 points: innovation, business impact, technical execution, Agentia extensibility, and presentation. Functionality must match the demo. The rules name CST but do not specify a cutoff hour in the text inspected; aim to submit October 25. [Official event page and rules modal](https://developer.copado.com/hackathon/).

| Criterion | What ReleaseProof should demonstrate |
| --- | --- |
| Innovation | A current green test suite misses a business defect; a requirement-derived check exposes it, and a subsequent change invalidates the appropriate evidence. |
| Impact | Measured time to obtain a release decision, concrete defects detected, and regression checks reused from earlier incidents. |
| Technical execution | One complete live journey, reliable failure handling, restart persistence, source links, and reproducible evaluation cases. |
| Agentia extensibility | Actual Agentia collection/execution plus a reusable headless workflow that also works without the web UI. |
| Presentation | A single business story with a visible before/failure/fix/recheck sequence. |

These are our execution priorities, not predicted judging scores.

## What already exists in the market

Copado advertises requirement-driven test creation, org-aware analysis, automated execution, and deployment capabilities. Generic “AI analyzes changes and generates tests” substantially overlaps its own positioning. [Copado AI platform](https://www.copado.com/ai-platform).

Gearset documents metadata dependency exploration and change-impact visibility. A dependency graph by itself is not a strong novelty claim. [Gearset Org Intelligence](https://docs.gearset.com/en/articles/11831993-org-intelligence).

Panaya already documents Salesforce impact analysis and risk-based testing. “Run only relevant tests” is established product territory. [Panaya ForeSight documentation](https://success.panaya.com/docs/foresight).

Mutation testing deliberately alters behavior to test whether a suite detects it; the technique is established. Our first deliverable should be requirement-derived counterexample tests. A full mutation engine is an optional later validation technique, not something we claim to invent. [Stryker explanation](https://stryker-mutator.io/docs/).

Revision-bound attestations also exist. Their relevance here is the principle of checking that evidence applies to the artifact being evaluated. ReleaseProof should not claim SLSA compliance from adding a hash field. [SLSA source verification](https://slsa.dev/spec/v1.2/verifying-source).

**Our defensible differentiation hypothesis:** combine executable business obligations, incident-derived regression requirements, and change-sensitive evidence into one headless Salesforce release decision. The reviewed sources establish overlap in the ingredients; they do not establish that no competitor offers the combination. Demonstrate the exact workflow and its measured behavior instead of saying “world first.”

## Current implementation findings

The app is a useful UI scaffold, but its evidence engine is currently mostly demonstration data.

| Finding from local source | Consequence | Required change |
| --- | --- | --- |
| `backend/main.py` and `server.py` always return READY FOR UAT. | Failed, missing, or wrong-environment evidence cannot change the conclusion. | One shared deterministic policy engine; backend owns every recommendation. |
| `web/app/page.tsx` separately hardcodes readiness, some counts, and historical similarity. | Correcting only the API would leave misleading screen content. | Render every status and count from validated response data. |
| `web/app/api/status/route.ts` equates backend health with Agentia connection. | Demo mode appears live/authenticated. | Independent backend, CLI, CI/CD, CRT, and AI capability states. |
| The analyze proxy returns demo evidence on exceptions. | Failed live analysis can look like successful evidence collection. | Explicit demo/replay/live modes; preserve errors in live mode. |
| The adapter maps an unavailable health check to passed. | Missing data becomes positive evidence. | Unknown/error stays unknown/error; health is separate from release validation. |
| Graph edges, counts, and INC-1042 are fixed. | Graph is not an explanation of actual evidence. | Build nodes and typed edges from stored records. |
| The real adapter returns no dependencies or historical patterns. | Core impact/memory claims remain unimplemented. | Add normalized dependency input and structured incident persistence. |
| Tests run via a generic work command without explicit repository context. | Wrong work context or unproven test provenance. | Configured Salesforce repository, work item, revision, and environment binding. |
| No actual model call, claim verifier, or historical retrieval is present in the inspected backend. | “Intent agent” currently describes a planned capability. | Add bounded structured extraction, then execution-based verification. |
| Logic is duplicated in two Python servers. | Behavior and failure handling can diverge. | Extract a shared engine used by both entry points. |

The current shell did not find `agentia` on PATH. That does not prove it is absent elsewhere; live integration readiness remains unverified.

## Three signature capabilities

### 1. Executable business contracts and counterexamples — highest priority

Example requirement: “Only leads with a score greater than 80 go to the Senior Sales queue.”

Normalize the requirement into a reviewed expectation with inputs, predicates, outcomes, actor, environment, source reference, and ambiguity flags. For the demo, use an integer-valued score domain explicitly. Generate checks for 79, 80, and 81. Null handling and other domains must come from an explicit requirement, not an invented default.

If the code uses `>= 80`, a test at 80 should show the expected Standard queue and observed Senior queue. Show the requirement text, relevant source location, assertion, real runner result, and log reference together. The LLM's suspicion alone remains a hypothesis until execution establishes the counterexample.

Implementation scope: one narrow rule family, Salesforce Lead routing, with a small catalog of boundary and authorization templates. Use the model to extract and explain; use a schema validator and deterministic evaluator for evidence state. Ambiguous language produces a review item and blocks the relevant claim from becoming verified.

Expected outputs must come from the approved requirement, independently of the implementation being tested. Do not generate a test oracle by asking the same model to infer what the current code does. Freeze requirement contracts before evaluating the seeded defects.

Acceptance: the original suite passes on the seeded boundary defect; the additional requirement check fails; after the fix, the same check passes and the business claim changes state with its execution record attached.

### 2. Incident memory that creates required regression checks

Upgrade historical memory from a similarity card into an operational rule:

“This Flow and permission dependency participated in INC-1042. The reviewed prevention rule requires a standard-user routing check when that relationship changes.”

Store incident ID, provenance, affected components and relationship, actor, symptom, reviewed cause, reproduction steps, resolving change, linked regression test, applicability conditions, and review status. Match exact component/path overlap first. Use text similarity only as a retrieval aid with explainable matching reasons—not a 91% probability of failure.

An incident can suggest a test without proving that the current release contains the same bug. A relevant reviewed prevention rule makes its linked check mandatory; executing that check supplies the current evidence. A failed run can remain unresolved without being labeled a confirmed historical recurrence.

Start with a clearly labeled, synthetic historical incident and a structured JSON import. For a public demo, avoid private production data. Jira/ServiceNow ingestion and embeddings are later integrations.

Acceptance: import an incident, restart the app, analyze a relevant change, and see its regression check selected with the matching relationship explained. An unrelated change must not activate the same rule.

### 3. Evidence freshness and selective invalidation

Bind each evidence item to the inputs that matter: requirement version, source revision and relevant content digests, test version, environment identity and observed metadata snapshot, actor/permission configuration, dependency snapshot, policy version, and run ID/time.

When a relevant input changes, traverse its claim/evidence relationships and mark the affected evidence stale. Show the precise reason and a proposed recheck. A changed permission set can invalidate a persona claim while leaving an independent score-boundary check reusable, if its recorded dependencies support that conclusion. Unknown dependency completeness requires conservative invalidation or an explicit uncertainty state.

Read observed snapshots before deciding; do not pretend to monitor org changes continuously without a polling or event integration. If current target state cannot be retrieved, mark freshness unknown. A UAT result is evidence about UAT, not automatic verification of production.

Export a versioned evidence bundle and a verifier that rechecks its identity, completeness, policy, and available freshness inputs. Hashes detect changed content against a trusted recorded digest; hashes alone do not authenticate the issuer. Signed bundles are optional later work.

Acceptance: a passing decision becomes stale after a relevant code/permission change; a report lists the affected claims and checks. Updating an unrelated README leaves the claim current. Missing environment observations prevent a false “current” label.

## Supporting features and deliberate scope cuts

| Feature | Priority | Scope |
| --- | --- | --- |
| Correct decision engine, explicit modes, real Agentia execution, persistent evidence | P0 | Foundation before new novelty features. |
| Boundary counterexample | P0 | One end-to-end Apex/business behavior path. |
| Incident-to-regression obligation | P0 | One structured incident and two matching/nonmatching examples. |
| Freshness and invalidation | P0 | Source/test/requirement changes first; permission snapshot when observable. |
| Persona coverage | P1 | Two real actors, one permission-sensitive operation. |
| Suggested smallest useful recheck set | P1 | Greedy weighted coverage heuristic over known obligations, with mandatory checks retained. |
| Mutation challenge | Stretch | One isolated sandbox variant, only after the core works reliably. |
| Signed bundle, extra MCP server, elaborate native plugin | Stretch | Only if integration support and remaining time justify them. |
| Chatbot, Slack bot, many connectors, 3D graphs, autonomous production promotion | Defer | Each introduces work outside the signature demonstration. |

A persona view should show which operation succeeded or failed for which actor, not just a role badge. Salesforce documents distinct object/field access behavior and user-mode controls; privileged success does not establish ordinary-user behavior. [Salesforce secure coding guidance](https://developer.salesforce.com/docs/platform/secure-coding/guide/secure-coding-access-control-protect-from-crud-fls-vulnerabilities.html).

For test selection, report coverage of modeled obligations, not guaranteed total application coverage. A budget may postpone optional checks but cannot silently waive mandatory ones. If no test covers an obligation, display the gap. Do not call a greedy selection mathematically minimal.

## Proposed architecture and live integration

Retain Next.js/React, the PWA shell, Python/FastAPI, and the current visual direction. Add SQLite tables for analyses, contracts, obligations, components, typed edges, runs, artifacts, incidents, policies, and decision versions. SQLite is sufficient for this prototype; no separate graph database is needed initially.

One engine should serve both a local headless CLI and the web API:

`CLI or web request → collector → contract/impact planner → evidence executor → policy evaluator → SQLite + evidence bundle`

Run long tests asynchronously with persisted jobs, polling, timeouts, terminal states, and duplicate-run protection. Preserve raw artifact references alongside normalized facts. Redact secrets from exported logs. Test one pinned Agentia version and record its version with the analysis.

**Integration constraints checked in official documentation:** Agentia's documented dependency operations require Source Format pipelines. CRT has separate readiness checks. The plugin SDK currently exposes limited host capabilities and does not allow plugins to wrap arbitrary commands or register their own tools into Agentia MCP. Therefore, use an external orchestrator with the supported CLI first; add a small native plugin only within supported SDK boundaries. [Agentia documentation](https://developer.copado.com/docs).

**Execution mapping:** collect the story with `cicd work get`; collect impact with `cicd metadata dependency list`; obtain local gate results with `cicd work test`; run CRT with `testing build run`, then poll `testing build get` and collect `testing build logs`. Run repository-sensitive operations in the configured Salesforce checkout. Confirm flags and result schemas against the installed CLI before implementing parsing. These operations have different purposes: organization health is not target deployment validation, and starting a job is not a passing test. [Agentia workflows](https://developer.copado.com/guides).

Keep live collection and live execution explicit. Demo fixtures and recorded replay are useful for reviewer reproducibility, but should have persistent visible labels. A replay reruns the local decision logic on recorded evidence; it does not establish the current state of a remote org.

Proposed ReleaseProof commands (new commands to implement, not existing Agentia commands):

```text
releaseproof analyze US-247 --environment UAT --json
releaseproof run-checks <analysis-id> --json
releaseproof verify <bundle-path> --json
releaseproof explain <claim-id> --json
```

Separate evidence readiness from human authorization. A human acceptance of an exception records a decision; it does not change an unverified claim into a verified one. Suggested decision states: blocked by failed check, insufficient evidence, stale evidence, and evidence requirements satisfied / awaiting approval. Every decision carries applicable policy and unresolved findings.

Agent behavior should be visible in the run history: inspect a gap, propose a check, execute it through the allowed runner, consume the result, and update the decision. Multiple agent names are not evidence of agentic behavior. A single bounded orchestrator is sufficient.

## Product changes

Make the primary view a release decision with an actionable reason:

```text
US-247 / UAT / revision abc123 / LIVE
BLOCKED — the score-80 boundary violates AC-2

Requirement        Expected        Observed       Evidence
Score = 80         Standard       Senior         Run 583 / assertion 2

Next check: rerun LeadRoutingBoundary after the fix
```

Use three focused views: Decision, Evidence, and History. Show a compact business path in the decision view and expand the graph only when the user needs to trace a relationship. The graph should answer “why is this test required?” or “why did this evidence become stale?”

Keep the neutral console palette. Reserve status colors for actual result states, show text/icons as well as color, and improve contrast on muted labels. Use motion only for execution or state changes. Remove fake connection rows, inert options, arbitrary confidence percentages, and decorative metrics.

Primary actions: inspect finding, run proposed checks, compare decision versions, and export evidence. Show timestamps, mode, target, and revision together. Cached PWA data remains visibly cached; offline display must not suggest live validation.

## Evaluation plan

Create eight versioned cases with expected results fixed before the final evaluation:

| Case | Expected observation |
| --- | --- |
| Correct boundary implementation | Relevant claim verified after the matching run. |
| `>` changed to `>=` | Existing suite passes; boundary check finds the seeded defect. |
| Required permission omitted | Ordinary-user check fails or remains unverified until executable evidence exists. |
| Previously documented failure relationship recurs | Incident rule selects the linked regression test. |
| Unrelated metadata change | That incident rule is not selected. |
| Source/test version changes after pass | Affected evidence becomes stale. |
| Target/actor differs from recorded result | Result cannot verify that new context. |
| Timeout, missing artifact, or unavailable connector | Insufficient evidence; no fabricated success. |

Also exercise empty requirements, malformed upstream JSON, repeated requests, and a server restart. Add an unrelated-file control to test overly broad invalidation. Failed/flaky evidence remains unresolved unless an explicit reviewed policy explains how to treat it.

Compare the same cases under (A) existing checks and (B) existing checks plus ReleaseProof. Record seeded-defect detection, false-ready cases, unnecessary blockers, verified claims/required claims, time to first actionable finding, number of tests selected/executed, and wall-clock time. Identify setup, queue time, and execution time separately. Any tests-run reduction should disclose its obligation coverage and missed defects.

Report raw counts and limitations. A small synthetic benchmark supports a demo, not a general accuracy or incident-reduction percentage. Reserve unseen threshold values or an unseen permission variant to check that behavior is not hardcoded to US-247.

## Suggested delivery sequence

This is an estimate assuming one focused builder and working Copado access; dates are planning targets, not promises.

| Dates | Deliverable | Exit condition |
| --- | --- | --- |
| Oct 12–13 | Capability inventory, truthful states, shared policy engine, configured demo Salesforce project | Failed/unknown evidence cannot appear ready; one authentic CI/CD read and CRT readiness check recorded. |
| Oct 14–16 | Persisted contracts, runs, and requirement counterexample | Boundary defect fails in the actual test target and passes after fix. |
| Oct 17–18 | Incident memory and persona regression | Historical relationship selects a real check; unrelated case does not. |
| Oct 19–20 | Evidence versions, invalidation, bundle verifier, headless workflow | Relevant change invalidates evidence and produces a recheck plan. |
| Oct 21–22 | Focused UI and eight-case evaluation | UI/CLI agree; restart and error cases work; measurements saved. |
| Oct 23–24 | Feature freeze, recording, deck, clean installation rehearsal | Another person can follow the README and reproduce the labeled scenario. |
| Oct 25 | Submission buffer | Repository, video, and deck accessible; claims match implemented behavior. |

If live access is unavailable after the first phase, reduce scope immediately to a transparent recorded-evidence prototype and pursue the missing environment access in parallel. Do not spend the remaining build window adding dashboards while execution remains unverified. If time slips, cut mutation testing, automatic remediation, extra connectors, native plugin packaging, and graph polish before cutting real evidence or error handling.

## Five-minute demonstration

| Time | Scene |
| --- | --- |
| 0:00–0:30 | Explain the lead-routing requirement and show the original test suite passing. |
| 0:30–1:00 | Invoke ReleaseProof from the terminal/IDE and show real Agentia collection. |
| 1:00–2:00 | Show the score-80 counterexample, expected/actual result, and blocked decision. |
| 2:00–2:40 | Open the historical incident relationship and show the persona regression it adds. |
| 2:40–3:30 | Apply the prepared reviewed fix, execute relevant checks, and show new evidence. |
| 3:30–4:10 | Change a relevant permission/source input; show stale evidence and the precise recheck. |
| 4:10–4:40 | Inspect the versioned bundle, mode, revision, environment, and approval state. |
| 4:40–5:00 | Present measured benchmark outcomes and the concrete Agentia extension value. |

Use edited footage with visible run IDs/times if remote jobs take longer than the video; do not imply instant execution. Seeded defects and historical incidents should be labeled. Keep a reproducible replay path for reviewers and a recording of actual integration execution.

Suggested deck: business problem; shortcomings of pass/fail counts; the executable contract workflow; Agentia integration and architecture; demonstration results; limitations and next steps.

Closing pitch: **“ReleaseProof shows which business promises this release has verified, exposes the missing checks, and knows when its evidence is out of date.”**
