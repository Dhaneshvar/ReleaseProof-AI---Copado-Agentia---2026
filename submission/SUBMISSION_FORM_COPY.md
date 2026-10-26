# ReleaseProof AI hackathon submission copy

## Submission title

ReleaseProof AI: Evidence-Driven Release Intelligence for Copado Agentia

## Problem statement

AI-assisted development and CI/CD make teams faster, but a green build does not always prove that a release satisfies the business contract. Teams commonly test happy paths while missing boundary conditions, permission behavior, regression impact, or evidence that became stale after a change. The result is a release decision based on incomplete proof. Release managers need a clear answer to a harder question than “did the tests pass?”: “did we prove the behavior that matters, and can we explain the decision?”

## Abstract / description of solution

ReleaseProof AI is an evidence-driven release intelligence layer for Copado Agentia. It turns a business requirement and work item into a verifiable evidence plan, then presents the checks, results, evidence freshness, assumptions, and release decision in one traceable view.

The demo models a Salesforce lead-routing change. The contract says scores greater than 80 route to Senior Sales, scores 80 or below route to Standard Sales, and only Sales Managers can override routing. Existing examples cover scores 60 and 100, but omit the equality boundary at 80 and the permission rule. ReleaseProof identifies the missing proof, runs the required checks, exposes the incorrect score-80 behavior, blocks the decision, and re-runs the evidence after the modeled fix.

The product is local-first for reproducible quality gates and includes an Agentia adapter for Copado work-item context, local checks, and future live Copado Robotic Testing evidence. It complements Copado Agentia by making Plan, Build, and Test evidence explainable at release time.

## Problem solved / gap addressed

ReleaseProof addresses the gap between code-level test results and business-level release confidence.

Most release tooling can show that a build completed or that selected tests passed. It is harder to see which parts of a business contract remain unverified, which evidence is stale because of a change, and why a release should be approved or blocked.

ReleaseProof solves this by:

- representing the business rule as an explicit contract;
- identifying missing boundary, permission, and regression checks;
- separating passed, failed, stale, and unverified evidence;
- explaining the release decision and the next action;
- preserving an evidence version and exportable JSON record; and
- providing a local deterministic mode that teams can run before external credentials are available.

The result is a release decision that is inspectable and defensible instead of an unexplained confidence score.

## Tools / technologies used

Next.js, React, TypeScript, PWA patterns, FastAPI, Python, Agentia CLI adapter, Copado CI/CD and CRT connector design, deterministic local evidence engine, JSON evidence export, Git, PowerShell.

## Public GitHub repository link

Paste the public GitHub repository URL here after pushing the project. Do not submit a localhost URL.

## Any comments or considerations

The recorded demo uses LOCAL DEMO mode so the judging flow remains deterministic and does not depend on private Copado credentials. The Agentia/Copado live connector is designed for invited Copado organizations and can be enabled through the Agentia CLI when the organization, pipeline, and CRT permissions are available. No credentials or customer data are included in the repository or recording.

## 2-minute demo script

This is ReleaseProof AI, an evidence-driven release intelligence layer for Copado Agentia.

The problem is that a green test result does not always prove that a release is safe. Teams often test normal cases but miss boundaries, permissions, or evidence invalidated by a change.

Here, work item US-247 changes Salesforce lead routing. The business rule says scores greater than 80 go to Senior Sales, while 80 or below go to Standard Sales. Existing examples test 60 and 100, but they do not test the equality boundary at 80.

I will analyze the work item. ReleaseProof marks the evidence as incomplete because the required proof is missing. After I run the required checks, the boundary check fails: score 80 is routed to Senior Sales instead of Standard Sales.

I will apply the modeled boundary fix and run the checks again. The evidence is now satisfied, and the application can export the checks, evidence version, assumptions, and decision as a JSON record.

ReleaseProof does not replace Copado Agentia. It adds a transparent evidence layer around the Plan, Build, and Test workflow so teams can answer: did we prove the business contract?
