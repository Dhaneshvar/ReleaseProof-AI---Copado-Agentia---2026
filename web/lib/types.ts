export type CheckState = "passed" | "failed" | "stale" | "unverified";
export type EvidenceResult = {
  run_id: string; at: string; revision: string; environment: string; runner: string;
  input_hashes: Record<string, string>; input: string; expected: string; actual: string;
  status: CheckState; log: string; artifact_digest: string;
};
export type Check = {
  id: string; title: string; kind: string; actor: string; dependencies: string[];
  source: string; reason: string; status: CheckState; result: EvidenceResult | null; stale_reason: string | null;
};
export type Incident = {
  id: string; title: string; components: string[]; root_cause: string; actor: string;
  regression_kind: string; reviewed: boolean; synthetic: boolean; provenance: string;
  matched_components?: string[]; match_reason?: string;
};
export type Decision = {
  state: "blocked" | "stale" | "insufficient" | "satisfied";
  title: string; reason: string; policy: string; approval: string; scope: string;
};
export type Run = {
  id: string; analysis_id: string; analysis_version: number; status: string; selected: string[];
  detail: string; created_at: string;
};
export type Analysis = {
  id: string; version: number; work_item_id: string; title: string; environment: string; mode: "demo" | "live";
  created_at: string; updated_at: string; requirements: string; runner: string; limitations: string[];
  config: { inclusive?: boolean; permission?: boolean; threshold?: number; scenario?: string };
  snapshot: {revision: string; environment: string; complete: boolean; parts: Record<string,string>; observed_at_source: string};
  decision: Decision; summary: { passed: number; failed: number; stale: number; unverified: number; total: number };
  checks: Check[]; incidents: Incident[]; components: string[]; warnings: string[];
  baseline: {input: string; expected: string; actual: string; status: string}[];
  recheck_plan: {id: string; title: string; reason: string}[];
  runs: {id: string; at: string; selected: string[]; runner: string}[];
  events: {at: string; action: string; detail: string}[];
  graph: {nodes: {id: string; label: string; kind: string; status?: string}[]; edges: {from: string; to: string; relationship: string; reason: string}[]};
  live_results: {name: string; status: string; detail?: string; build_id?: string; artifact?: unknown}[];
  active_run?: Run | null;
};
export type AnalysisSummary = Pick<Analysis,"id"|"version"|"work_item_id"|"title"|"environment"|"mode"|"updated_at"|"decision"|"summary">;
export type Capabilities = {
  backend: string; cli: string; repository: string; cicd: string; crt: string; ai: string;
  live_ready: boolean; detail: string; required_configuration: string[];
};
export type Bundle = {format: string; analysis: Analysis; sha256: string; integrity_note: string};
export type Verification = {integrity: boolean; matches_local_record: boolean; freshness: string; stale_checks: string[]; valid: boolean; detail: string};
export type Comparison = {from_version: number; to_version: number; from_decision: string; to_decision: string; changes: {id: string; title: string; before: string; after: string}[]};

