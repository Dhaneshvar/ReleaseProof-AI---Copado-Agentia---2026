"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowDownToLine, ArrowRight, Check, ChevronRight, CircleHelp, Clock3, FileCheck2, FlaskConical, GitBranch, Loader2, Play, Plug, RefreshCw, ShieldCheck, X } from "lucide-react";
import type { Analysis, AnalysisSummary, Bundle, Capabilities, Check as EvidenceCheck, Comparison, Incident, Run, Verification } from "../lib/types";
import { SCENARIOS } from "../lib/demo";

type Tab = "decision" | "evidence" | "history" | "connections";
const button = "inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-line px-4 py-2 text-sm font-medium transition hover:border-stone-500 disabled:cursor-not-allowed disabled:opacity-40";
const primary = button + " border-accent bg-accent text-ink hover:bg-[#ddff9f]";
const input = "min-h-11 w-full rounded-md border border-line bg-ink px-3 py-2 text-sm text-stone-200 outline-none focus:border-accent";
const incidentExample = JSON.stringify({ id: "INC-2048", title: "Routing threshold equality", components: ["LeadScoreRouter.model"], root_cause: "Equality was included in a strict greater-than condition.", regression_kind: "boundary", actor: "Routing service", reviewed: true, provenance: "Synthetic regression example" }, null, 2);

async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch("/api/" + path, { method: body === undefined ? "GET" : "POST", headers: { "Content-Type": "application/json" }, body: body === undefined ? undefined : JSON.stringify(body), cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "The request failed.");
  return data as T;
}
function stamp(value: string) { return new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" }); }
function Badge({ state }: { state: string }) {
  const good = ["passed", "satisfied", "current", "available", "connected", "ready", "configured", "completed"].includes(state);
  const bad = ["failed", "blocked"].includes(state);
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[11px] ${good ? "border-accent/25 bg-accent/5 text-accent" : bad ? "border-red-400/30 bg-red-400/5 text-red-300" : "border-amber/30 bg-amber/5 text-amber"}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{state.replaceAll("_", " ")}</span>;
}
function Modal({ check, close }: { check: EvidenceCheck; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} onClose={close} className="m-auto max-h-[90vh] w-[min(640px,94vw)] overflow-y-auto rounded-xl border border-line bg-surface p-6 text-stone-200 backdrop:bg-black/70">
    <div className="flex items-start justify-between gap-5"><div><p className="font-mono text-xs text-stone-400">{check.id} / {check.actor}</p><h2 className="mt-3 text-xl font-semibold">{check.title}</h2></div><button autoFocus onClick={() => ref.current?.close()} aria-label="Close evidence detail" className={button + " px-2"}><X size={18} /></button></div>
    <div className="my-5"><Badge state={check.status} /></div>
    <p className="text-sm leading-6 text-stone-400">{check.reason}</p>
    {check.stale_reason && <p className="mt-4 rounded-md border border-amber/30 p-3 text-sm text-amber">{check.stale_reason}. The result below is historical and must be rechecked.</p>}
    {check.result ? <><dl className="mt-6 space-y-4 text-sm">{[["Input", check.result.input], ["Expected", check.result.expected], ["Observed", check.result.actual], ["Runner", check.result.runner], ["Run", check.result.run_id], ["Revision / target", check.result.revision + " / " + check.result.environment], ["Executed", stamp(check.result.at)]].map(([label, value]) => <div key={label} className="grid grid-cols-[110px_1fr] gap-3 border-b border-line pb-3"><dt className="text-stone-400">{label}</dt><dd className="break-words font-mono text-xs">{value}</dd></div>)}</dl><pre className="mt-5 whitespace-pre-wrap break-words rounded-md bg-ink p-4 font-mono text-xs leading-6">{check.result.log}</pre><details className="mt-4 text-xs text-stone-400"><summary className="cursor-pointer">Input fingerprints and artifact digest</summary><pre className="mt-3 overflow-x-auto">{JSON.stringify({ inputs: check.result.input_hashes, artifact_digest: check.result.artifact_digest }, null, 2)}</pre></details></> : <p className="mt-6 rounded-md border border-dashed border-line p-5 text-sm text-stone-400">No execution evidence yet. This requirement has not been marked verified.</p>}
  </dialog>;
}

export default function Page() {
  const [tab, setTab] = useState<Tab>("decision");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [versions, setVersions] = useState<AnalysisSummary[]>([]);
  const [cap, setCap] = useState<Capabilities | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [workItem, setWorkItem] = useState("US-247");
  const [target, setTarget] = useState("UAT");
  const [mode, setMode] = useState<"demo" | "live">("demo");
  const [scenario, setScenario] = useState("boundary_bug");
  const [threshold, setThreshold] = useState(80);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [job, setJob] = useState<Run | null>(null);
  const [detail, setDetail] = useState<EvidenceCheck | null>(null);
  const [cached, setCached] = useState(false);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);
  const [incidentText, setIncidentText] = useState(incidentExample);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [initializing, setInitializing] = useState(true);
  const active = !!job && ["queued", "running"].includes(job.status);
  const disabled = busy || active || cached;

  const accept = (data: Analysis) => {
    if (!data.id || !Array.isArray(data.checks) || !data.decision) throw new Error("Unsupported analysis response.");
    setAnalysis(data); setCached(false); setDetail(null); setComparison(null); setVerification(null);
    try { localStorage.setItem("releaseproof-last", data.id); localStorage.setItem("releaseproof-cached", JSON.stringify(data)); } catch { /* Storage may be disabled. */ }
    if (data.active_run) setJob(data.active_run);
  };
  const refreshLists = async (id?: string) => {
    const list = await api<{ analyses: AnalysisSummary[] }>("analyses"); setAnalyses(list.analyses);
    if (id) setVersions((await api<{ versions: AnalysisSummary[] }>(`analyses/${id}/history?refresh=${Date.now()}`)).versions);
  };
  const refreshAnalysis = () => perform(async () => {
    setAnalysis(null); setJob(null); setVersions([]); setDetail(null); setComparison(null); setVerification(null); setCached(false); setTab("decision");
    try { localStorage.removeItem("releaseproof-last"); localStorage.removeItem("releaseproof-cached"); } catch { /* Storage may be disabled. */ }
    setNotice("Workspace cleared. Start a fresh analysis below. History remains available for audit.");
  });
  const perform = async (action: () => Promise<void>) => {
    setBusy(true); setError(""); setNotice("");
    try { await action(); } catch (err) { setError(err instanceof Error ? err.message : "Request failed."); } finally { setBusy(false); }
  };
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [capability, list, memory] = await Promise.all([api<Capabilities>("capabilities"), api<{ analyses: AnalysisSummary[] }>("analyses"), api<{ incidents: Incident[] }>("incidents")]);
        if (cancelled) return;
        setCap(capability); setAnalyses(list.analyses); setIncidents(memory.incidents);
        // Start each browser session with a clean workspace. Historical analyses remain in the History view.
        if (!cancelled) { setAnalysis(null); setVersions([]); setCached(false); }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Unable to connect.");
      } finally { if (!cancelled) setInitializing(false); }
    })();
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    if (!job || !["queued", "running"].includes(job.status)) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const next = await api<Run>("jobs/" + job.id);
        if (cancelled) return;
        setJob(next);
        if (next.status === "completed") {
          accept(await api<Analysis>("analyses/" + next.analysis_id)); await refreshLists(next.analysis_id);
          setNotice("Execution finished. The decision now reflects the recorded results.");
        } else if (["failed", "interrupted"].includes(next.status)) setError(next.detail);
        else timer = setTimeout(poll, 1000);
      } catch (err) { if (!cancelled) { setError(err instanceof Error ? err.message : "Run status unavailable."); timer = setTimeout(poll, 4000); } }
    };
    timer = setTimeout(poll, 500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [job?.id, job?.status]);

  const create = () => perform(async () => {
    const data = await api<Analysis>("analyze", { work_item_id: workItem, environment: target, mode, scenario, threshold });
    accept(data); setJob(null); setTab("decision"); await refreshLists(data.id);
  });
  const run = () => perform(async () => {
    if (analysis) setJob(await api<Run>(`analyses/${analysis.id}/run`, { expected_version: analysis.version }));
  });
  const change = (action: string, environment?: string) => perform(async () => {
    if (!analysis) return;
    accept(await api<Analysis>(`analyses/${analysis.id}/change`, { action, environment, expected_version: analysis.version }));
    setNotice("Input change recorded. Only dependent evidence needs a recheck."); await refreshLists(analysis.id);
  });
  const download = () => perform(async () => {
    if (!analysis) return;
    const bundle = await api<Bundle>(`analyses/${analysis.id}/bundle`);
    const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = analysis.id + "-v" + bundle.analysis.version + ".json"; link.click(); URL.revokeObjectURL(url);
    setNotice("Versioned evidence bundle downloaded. It is unsigned and is not a deployment approval.");
  });
  const inspectBundle = (file?: File) => perform(async () => {
    if (!file) return;
    if (file.size > 1_000_000) throw new Error("Choose an evidence bundle smaller than 1 MB.");
    setVerification(await api<Verification>("verify", JSON.parse(await file.text())));
  });
  const checks = analysis?.checks.filter(check => (filter === "all" || check.status === filter) && (check.title + check.id + check.actor).toLowerCase().includes(query.toLowerCase())) || [];
  const failed = analysis?.checks.find(check => check.status === "failed");

  return <div className="min-h-screen bg-ink text-stone-200">
    <header className="border-b border-line"><div className="mx-auto flex max-w-[1360px] flex-wrap items-center justify-between gap-4 px-5 py-5 sm:px-9">
      <a href="/" className="flex items-center gap-3" aria-label="ReleaseProof home"><span className="grid h-9 w-9 place-items-center rounded-lg bg-accent text-ink"><FileCheck2 size={21} /></span><span className="text-lg font-semibold tracking-tight">ReleaseProof<span className="ml-2 font-mono text-xs font-normal text-stone-500">AI</span></span></a>
      <div className="flex items-center gap-3 font-mono text-xs"><span className="hidden text-stone-500 sm:inline">POWERED BY COPADO AGENTIA</span><button onClick={() => setTab("connections")} className="rounded-full border border-line px-3 py-2 text-stone-300"><Plug size={12} className="mr-2 inline" />{cap?.live_ready ? "CI/CD connected" : "Live setup pending"}</button></div>
    </div></header>
    <main className="mx-auto max-w-[1360px] px-5 pb-12 sm:px-9">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line py-5">
        <nav aria-label="Workspace views" className="flex gap-1">{(["decision", "evidence", "history", "connections"] as Tab[]).map(item => <button key={item} onClick={() => setTab(item)} aria-current={tab === item ? "page" : undefined} className={`rounded-md px-3 py-2 text-sm capitalize ${tab === item ? "bg-stone-200 text-ink" : "text-stone-400 hover:text-stone-100"}`}>{item}</button>)}</nav>
        <span className="font-mono text-xs text-stone-500">RELEASE / EVIDENCE LEDGER</span>
      </div>
      {error && <div role="alert" className="mt-5 flex items-start justify-between gap-4 rounded-lg border border-red-400/30 bg-red-400/5 p-4 text-sm leading-6 text-red-200"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError("")}><X size={16} /></button></div>}
      {notice && <p role="status" className="mt-5 rounded-lg border border-line p-4 text-sm text-stone-300">{notice}</p>}
      {cached && <div role="status" className="mt-5 rounded-lg border border-amber/40 p-4 text-sm text-amber">Offline copy · saved {analysis ? stamp(analysis.updated_at) : ""}. Freshness is unknown. Actions are disabled until the service reconnects.<button onClick={() => window.location.reload()} className="ml-3 underline">Reconnect</button></div>}
      {initializing && <p className="flex items-center gap-3 py-10 text-sm text-stone-400"><Loader2 className="animate-spin" size={18} />Opening the evidence ledger…</p>}

      {(tab === "decision" || tab === "evidence") && <>
        <section className="grid gap-8 border-b border-line py-8 lg:grid-cols-[1fr_1.1fr]">
          <div><p className="font-mono text-xs uppercase tracking-[.18em] text-stone-500">A business promise. A verifiable check.</p><h1 className="mt-4 max-w-md text-3xl font-medium leading-tight tracking-tight sm:text-4xl">Every release should<br /><span className="text-stone-500">show its work.</span></h1><p className="mt-4 max-w-md text-sm leading-6 text-stone-400">See what was checked, what failed, and what needs new evidence when a release changes.</p></div>
          <div className="rounded-xl border border-line bg-surface p-5">
            <div className="mb-4 flex items-center justify-between"><h2 className="text-sm font-medium">Start an analysis</h2><select aria-label="Evidence mode" value={mode} onChange={e => setMode(e.target.value as "demo" | "live")} className="rounded border border-line bg-ink px-2 py-1 font-mono text-xs"><option value="demo">LOCAL DEMO</option><option value="live">LIVE COPADO</option></select></div>
            <div className="grid grid-cols-[1fr_100px] gap-3"><label className="text-xs text-stone-400">Work item<input className={input + " mt-2"} value={workItem} maxLength={80} onChange={e => setWorkItem(e.target.value)} /></label><label className="text-xs text-stone-400">Target<select className={input + " mt-2"} value={target} onChange={e => setTarget(e.target.value)}>{["DEV", "QA", "UAT", "PROD"].map(t => <option key={t}>{t}</option>)}</select></label></div>
            {mode === "demo" && <div className="mt-3 grid grid-cols-[1fr_100px] gap-3"><label className="text-xs text-stone-400">Scenario<select className={input + " mt-2"} value={scenario} onChange={e => setScenario(e.target.value)}>{SCENARIOS.map(s => <option value={s.id} key={s.id}>{s.label}</option>)}</select></label><label className="text-xs text-stone-400">Threshold<input type="number" min={1} max={999} className={input + " mt-2"} value={threshold} onChange={e => setThreshold(Number(e.target.value))} /></label></div>}
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3"><p className="max-w-[260px] text-xs leading-5 text-stone-500">{mode === "demo" ? "Executes a local reference model. No Salesforce or Copado run is simulated as live." : "Requires configured Agentia access. Live failures never fall back to demo results."}</p><button className={primary} onClick={create} disabled={busy || active || !workItem || (mode === "live" && !cap?.live_ready)}>{busy ? <Loader2 size={15} className="animate-spin" /> : <ArrowRight size={15} />}Analyze</button></div>
          </div>
        </section>
        {analysis ? <>
          <div className="flex flex-wrap items-center justify-between gap-4 py-6"><div className="flex flex-wrap items-center gap-3"><span className="rounded bg-panel px-2 py-1 font-mono text-xs text-stone-300">{analysis.mode === "demo" ? "LOCAL MODEL" : "LIVE COLLECTION"}</span><h2 className="font-semibold">{analysis.work_item_id} <span className="font-normal text-stone-400">/ {analysis.environment}</span></h2><span className="font-mono text-xs text-stone-500">v{analysis.version} · {analysis.snapshot.revision.slice(0, 12)}</span></div><div className="flex gap-2"><button className={button} disabled={disabled} onClick={download}><ArrowDownToLine size={14} />Export evidence</button><button className={button} disabled={busy || active} aria-label="Clear workspace" onClick={refreshAnalysis}><RefreshCw size={14} />Clear workspace</button></div></div>
          {tab === "decision" && <div className="grid items-start gap-5 lg:grid-cols-[1.45fr_1fr]">
            <section className="rounded-xl border border-line bg-surface p-6 sm:p-7">
              <div className="flex items-center justify-between gap-3"><Badge state={cached ? "freshness_unknown" : analysis.decision.state} /><span className="font-mono text-xs text-stone-500">DECISION / {analysis.mode === "demo" ? "DEMO" : "LIVE"}</span></div>
              <h2 className="mt-6 text-2xl font-medium tracking-tight sm:text-3xl">{cached ? "Saved evidence snapshot" : analysis.decision.title}</h2><p className="mt-3 max-w-xl text-sm leading-6 text-stone-400">{analysis.decision.reason}</p>
              <div className="my-6 grid grid-cols-4 divide-x divide-line border-y border-line py-4">{[["Passed", analysis.summary.passed], ["Failed", analysis.summary.failed], ["Stale", analysis.summary.stale], ["Unverified", analysis.summary.unverified]].map(([name, value]) => <div className="px-3 first:pl-0" key={name}><p className="font-mono text-2xl">{value}</p><p className="mt-1 text-xs text-stone-500">{name}</p></div>)}</div>
              {failed?.result && <button onClick={() => setDetail(failed)} className="mb-6 w-full rounded-lg border border-red-400/25 bg-red-400/5 p-4 text-left"><p className="font-mono text-xs text-red-300">COUNTEREXAMPLE / {failed.id}</p><p className="mt-3 text-sm">{failed.result.input}</p><div className="mt-3 grid grid-cols-2 gap-3 text-sm"><div><span className="block text-xs text-stone-500">Expected</span><span className="mt-1 block">{failed.result.expected}</span></div><div><span className="block text-xs text-stone-500">Observed</span><span className="mt-1 block text-red-300">{failed.result.actual}</span></div></div><span className="mt-4 flex items-center gap-2 text-xs text-red-200">Inspect the assertion and run log <ArrowRight size={13} /></span></button>}
              <div className="flex flex-wrap items-center gap-3"><button className={primary} disabled={disabled || !analysis.recheck_plan.length || (analysis.mode === "live" && !cap?.live_ready)} onClick={run}>{active ? <Loader2 className="animate-spin" size={16} /> : <Play size={15} />}{active ? "Running checks…" : "Run required checks"}{!active && <span className="rounded bg-black/10 px-1.5 font-mono text-xs">{analysis.recheck_plan.length}</span>}</button><button onClick={() => setTab("evidence")} className={button}>Inspect evidence <ChevronRight size={15} /></button></div>
              {job && <p role="status" className="mt-3 font-mono text-xs text-stone-400">{job.id} · {job.status} · {job.detail}</p>}
              {analysis.mode === "demo" && analysis.runs.length > 0 && <section className="mt-6 rounded-lg border border-accent/20 bg-accent/[0.03] p-4"><div className="flex items-center justify-between gap-3"><div><p className="font-mono text-[10px] uppercase tracking-[.16em] text-accent">Agentia local trace</p><h3 className="mt-1 text-sm font-medium">Workflow replay · no Copado credentials used</h3></div><span className="rounded-full border border-accent/25 px-2 py-1 font-mono text-[10px] text-accent">DRY RUN</span></div><div className="mt-4 space-y-3 font-mono text-xs"><div className="flex items-start gap-3"><Check size={14} className="mt-0.5 text-accent" /><span><b className="font-normal text-stone-300">agentia cicd work get {analysis.work_item_id}</b><span className="mt-1 block text-stone-500">Loaded the work-item contract from the local demo fixture.</span></span></div><div className="flex items-start gap-3"><Check size={14} className="mt-0.5 text-accent" /><span><b className="font-normal text-stone-300">agentia cicd work test --local</b><span className="mt-1 block text-stone-500">Executed the ReleaseProof quality-gate model against required checks.</span></span></div><div className="flex items-start gap-3"><Check size={14} className="mt-0.5 text-accent" /><span><b className="font-normal text-stone-300">releaseproof evidence evaluate</b><span className="mt-1 block text-stone-500">Persisted evidence version {analysis.version} and recalculated the decision.</span></span></div></div></section>}
              <p className="mt-6 flex items-center gap-2 text-xs text-stone-500"><ShieldCheck size={14} />Evidence is not a deployment approval.</p>
            </section>
            <div className="space-y-5">
              <section className="rounded-xl border border-line p-5"><h3 className="flex items-center gap-2 text-sm font-medium"><FileCheck2 size={16} className="text-stone-400" />Business contract</h3><p className="mt-4 text-sm leading-6 text-stone-300">{analysis.requirements}</p><p className="mt-3 font-mono text-[11px] text-stone-500">{analysis.mode === "demo" ? "REVIEWED TEMPLATE / INTEGER SCORE DOMAIN" : "COPADO WORK ITEM / ASSERTIONS UNMAPPED"}</p></section>
              {analysis.baseline.length > 0 && <section className="rounded-xl border border-line p-5"><div className="flex items-center justify-between"><h3 className="text-sm font-medium">Existing example suite</h3><Badge state={analysis.baseline.every(c => c.status === "passed") ? "passed" : "failed"} /></div><div className="mt-3 space-y-2">{analysis.baseline.map(c => <div key={c.input} className="flex justify-between font-mono text-xs text-stone-400"><span>{c.input}</span><span>{c.actual}</span></div>)}</div><p className="mt-4 text-xs leading-5 text-stone-500">These checks omit equality and user permissions. Passing them does not verify the full contract.</p></section>}
              {analysis.mode === "demo" && <section className="rounded-xl border border-dashed border-line p-5"><h3 className="flex items-center gap-2 text-sm font-medium"><FlaskConical size={16} />Change the local model</h3><p className="mt-2 text-xs leading-5 text-stone-500">Observe which evidence becomes stale. These controls never modify Salesforce.</p><div className="mt-4 flex flex-wrap gap-2"><button disabled={disabled} onClick={() => change(analysis.config.inclusive ? "fix_boundary" : "introduce_boundary_bug")} className={button + " text-xs"}>{analysis.config.inclusive ? "Apply boundary fix" : "Introduce boundary bug"}</button><button disabled={disabled} onClick={() => change(analysis.config.permission ? "revoke_permission" : "restore_permission")} className={button + " text-xs"}>{analysis.config.permission ? "Remove permission" : "Restore permission"}</button><button disabled={disabled} onClick={() => change("unrelated_change")} className={button + " text-xs"}>Edit unrelated notes</button></div><label className="mt-4 block text-xs text-stone-500">Change the modeled target<select aria-label="Change modeled target" disabled={disabled} value={analysis.environment} onChange={e => change("change_environment", e.target.value)} className={input + " mt-2"}>{["DEV", "QA", "UAT", "PROD"].map(t => <option key={t}>{t}</option>)}</select></label></section>}
            </div>
          </div>}
          {tab === "evidence" && <>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-medium">The evidence behind the decision</h2><p className="mt-2 text-sm text-stone-500">Select a check to inspect inputs, expected behavior, and the recorded result.</p></div><button className={primary} disabled={disabled || !analysis.recheck_plan.length || (analysis.mode === "live" && !cap?.live_ready)} onClick={run}><Play size={14} />Run required checks</button></div>
            <div className="mb-4 grid gap-3 sm:grid-cols-[1fr_180px]"><input className={input} placeholder="Find a requirement, actor, or check…" aria-label="Search evidence" value={query} onChange={e => setQuery(e.target.value)} /><select className={input} aria-label="Filter evidence status" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All evidence</option>{["passed", "failed", "stale", "unverified"].map(s => <option key={s}>{s}</option>)}</select></div>
            <div className="overflow-hidden rounded-xl border border-line">{checks.map(check => <button key={check.id} onClick={() => setDetail(check)} className="flex w-full flex-wrap items-center gap-4 border-b border-line p-5 text-left last:border-0 hover:bg-surface"><span className="min-w-[70px] font-mono text-xs text-stone-500">{check.id}</span><span className="min-w-[180px] flex-1"><strong className="block text-sm font-medium">{check.title}</strong><span className="mt-1 block text-xs leading-5 text-stone-500">{check.actor} · {check.stale_reason || check.reason}</span></span><Badge state={check.status} /><ChevronRight size={16} className="text-stone-500" /></button>)}{!checks.length && <p className="p-8 text-sm text-stone-500">No checks match this filter.</p>}</div>
            <section className="mt-6 rounded-xl border border-line p-5"><h3 className="text-sm font-medium">Why these checks exist</h3><p className="mt-2 text-xs text-stone-500">Relationships generated from this analysis. Incident matches create required regression checks.</p><div className="mt-4 space-y-3">{analysis.graph.edges.map(edge => <div key={edge.from + edge.to} className="flex flex-wrap items-center gap-2 text-xs"><span className="rounded border border-line px-3 py-2 font-mono">{edge.from === "story" ? analysis.work_item_id : edge.from}</span><span className="flex items-center gap-2 text-stone-500">{edge.relationship}<ArrowRight size={12} /></span><button className="rounded border border-line px-3 py-2 font-mono hover:border-accent" onClick={() => setDetail(analysis.checks.find(c => c.id === edge.to) || null)}>{edge.to}</button><span className="text-stone-500">{edge.reason}</span></div>)}</div></section>
            {analysis.live_results.length > 0 && <section className="mt-6 rounded-xl border border-line p-5"><h3>Agentia runner results</h3><p className="mt-2 text-xs text-stone-500">Supplementary evidence. Unmapped business claims remain unverified.</p>{analysis.live_results.map((r, i) => <details key={i} className="mt-4 border-t border-line pt-3"><summary className="cursor-pointer text-sm">{r.name} · {r.status}</summary><p className="mt-2 text-sm text-stone-400">{r.detail}</p><pre className="mt-3 overflow-auto text-xs">{JSON.stringify(r.artifact, null, 2)}</pre></details>)}</section>}
          </>}
          {analysis.incidents.length > 0 && <section className="mt-6 rounded-xl border border-line p-5"><div className="flex items-center gap-2 text-sm font-medium"><Clock3 size={16} className="text-amber" />History that changes the test plan</div>{analysis.incidents.map(incident => <div key={incident.id} className="mt-4 grid gap-4 border-t border-line pt-4 md:grid-cols-[1fr_1fr_auto]"><div><span className="font-mono text-xs text-amber">{incident.id} · SYNTHETIC</span><h4 className="mt-2 text-sm">{incident.title}</h4><p className="mt-2 text-xs leading-5 text-stone-500">{incident.root_cause}</p></div><div><p className="text-xs leading-5 text-stone-400">{incident.match_reason}</p><p className="mt-2 text-xs leading-5 text-stone-500">{incident.provenance}</p></div><button className={button + " self-start text-xs"} onClick={() => setDetail(analysis.checks.find(c => c.source === incident.id) || null)}>Inspect regression <ArrowRight size={13} /></button></div>)}</section>}
          <details className="mt-6 rounded-lg border border-line p-4 text-sm text-stone-500"><summary className="cursor-pointer">Scope, assumptions, and limitations</summary><ul className="mt-3 list-disc space-y-2 pl-5 text-xs leading-5">{[...analysis.limitations, ...analysis.warnings].map((text, i) => <li key={i}>{text}</li>)}</ul></details>
        </> : !initializing && <div className="my-8 rounded-xl border border-dashed border-line px-6 py-10"><p className="font-mono text-xs text-accent">START WITH THE MISSED-BOUNDARY SCENARIO</p><h2 className="mt-3 text-xl">Passing examples can still miss the requirement.</h2><p className="mt-3 max-w-xl text-sm leading-6 text-stone-400">Analyze the work item, run its required checks, and inspect the score-80 counterexample. Apply the fix, recheck, then remove a permission to see evidence become stale.</p></div>}
      </>}

      {tab === "history" && <div className="py-8"><div className="mb-6 flex items-center justify-between"><div><h1 className="text-3xl font-medium tracking-tight">A record you can inspect.</h1><p className="mt-3 text-sm text-stone-400">Saved analyses, decision changes, and reusable incident knowledge.</p></div><button className={button} disabled={busy} onClick={() => perform(() => refreshLists(analysis?.id))}><RefreshCw size={14} />Refresh</button></div>
        <div className="grid gap-5 lg:grid-cols-[1fr_1fr]"><section className="rounded-xl border border-line p-5"><h2 className="mb-4 text-sm font-medium">Analysis ledger</h2>{analyses.map(item => <button disabled={busy || active} key={item.id} onClick={() => perform(async () => { accept(await api<Analysis>("analyses/" + item.id)); await refreshLists(item.id); setTab("decision"); setJob(null); })} className="flex w-full flex-wrap items-center justify-between gap-3 border-t border-line py-4 text-left"><span><strong className="block text-sm font-medium">{item.work_item_id} / {item.environment}</strong><span className="mt-1 block font-mono text-[11px] text-stone-500">{item.id} · v{item.version} · {item.mode}</span></span><Badge state={item.decision.state} /></button>)}{!analyses.length && <p className="text-sm text-stone-500">Your first analysis will appear here.</p>}</section>
          <section className="rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Decision versions {analysis && " / " + analysis.work_item_id}</h2><div className="mt-4 max-h-80 overflow-y-auto">{versions.map(v => <div key={v.version} className="flex flex-wrap items-center justify-between gap-3 border-t border-line py-3 text-xs"><span>v{v.version} · {stamp(v.updated_at)}</span><Badge state={v.decision.state} /><button disabled={busy || !analysis} className="text-accent underline decoration-accent/30 underline-offset-4" onClick={() => perform(async () => { if (analysis) setComparison(await api<Comparison>(`analyses/${analysis.id}/compare?version=${v.version}`)); })}>Compare with latest</button></div>)}</div>{comparison && <div className="mt-4 rounded-lg bg-panel p-4 text-xs"><p>v{comparison.from_version} → v{comparison.to_version} · {comparison.from_decision} → {comparison.to_decision}</p>{comparison.changes.map(c => <p className="mt-3 text-stone-400" key={c.id}>{c.id}: {c.before} → {c.after}</p>)}{!comparison.changes.length && <p className="mt-3 text-stone-500">No check statuses changed between these versions.</p>}</div>}</section>
        </div>
        {analysis && <section className="mt-5 rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Execution timeline / {analysis.work_item_id}</h2><div className="mt-4 space-y-4">{analysis.events.map((event, i) => <div key={i} className="grid gap-2 border-l border-line pl-4 sm:grid-cols-[160px_1fr]"><span className="font-mono text-xs text-stone-500">{stamp(event.at)}</span><div><p className="text-sm">{event.action.replaceAll("_", " ")}</p><p className="mt-1 text-xs text-stone-500">{event.detail}</p></div></div>)}</div></section>}
        <div className="mt-5 grid gap-5 lg:grid-cols-2"><section className="rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Verify an exported bundle</h2><p className="mt-2 text-xs leading-5 text-stone-500">Checks the content digest, stored original, and latest local input fingerprints. A valid bundle can still contain failed checks.</p><label className="mt-5 block text-xs text-stone-400">Evidence JSON<input disabled={busy} type="file" accept=".json,application/json" className="mt-2 block w-full rounded border border-line p-3 text-xs file:mr-3 file:rounded file:border-0 file:bg-stone-200 file:px-3 file:py-2 file:text-ink" onChange={e => { inspectBundle(e.target.files?.[0]); e.target.value = ""; }} /></label>{verification && <div className="mt-4 rounded-lg bg-panel p-4 text-sm"><p>Content integrity: {verification.integrity ? "matches" : "mismatch"}</p><p className="mt-2">Local record: {verification.matches_local_record ? "matches" : "unknown / altered"}</p><p className="mt-2">Freshness: <Badge state={verification.freshness} /></p>{verification.stale_checks.length > 0 && <p className="mt-3 text-amber">Recheck: {verification.stale_checks.join(", ")}</p>}<p className="mt-3 text-xs leading-5 text-stone-500">{verification.detail}</p></div>}</section>
          <section className="rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Incident memory / {incidents.length} records</h2><p className="mt-2 text-xs leading-5 text-stone-500">Import a reviewed local-model regression rule. It applies to new analyses with matching components.</p><details className="mt-4"><summary className="cursor-pointer text-sm text-stone-300">Import incident JSON</summary><textarea aria-label="Incident JSON" value={incidentText} onChange={e => setIncidentText(e.target.value)} rows={12} className={input + " mt-4 font-mono text-xs"} /><button className={button + " mt-3"} disabled={busy} onClick={() => perform(async () => { await api("incidents", JSON.parse(incidentText)); setIncidents((await api<{incidents: Incident[]}>("incidents")).incidents); setNotice("Incident saved. Create a new analysis to apply the reviewed rule."); })}>Save incident</button></details><div className="mt-4 space-y-3">{incidents.map(i => <details className="border-t border-line pt-3 text-xs" key={i.id}><summary className="cursor-pointer text-stone-300">{i.id} · {i.title}</summary><p className="mt-2 leading-5 text-stone-500">{i.root_cause}</p><p className="mt-2 leading-5 text-stone-500">{i.provenance}</p></details>)}</div></section></div>
      </div>}

      {tab === "connections" && <section className="py-8"><div className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-3xl font-medium tracking-tight">Know what is connected.</h1><p className="mt-3 max-w-xl text-sm leading-6 text-stone-400">Backend availability, CLI installation, and Copado authentication are separate checks. Demo execution never implies a live connection.</p></div><button disabled={busy} className={primary} onClick={() => perform(async () => { setCap(await api<Capabilities>("capabilities", {})); setNotice("Connection probes finished. No test or deployment was started."); })}>{busy ? <Loader2 className="animate-spin" size={15} /> : <Plug size={15} />}Check connections</button></div>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[["Evidence API", cap?.backend || "unknown"], ["Agentia CLI", cap?.cli || "unknown"], ["Salesforce repository", cap?.repository || "unknown"], ["Copado CI/CD", cap?.cicd || "unchecked"], ["Copado Robotic Testing", cap?.crt || "unchecked"], ["LLM interpretation", cap?.ai || "not_integrated"]].map(([name, status]) => <div key={name} className="rounded-xl border border-line bg-surface p-5"><h2 className="mb-4 text-sm font-medium">{name}</h2><Badge state={status} /></div>)}</div>
        <p className="mt-5 text-sm text-stone-400">{cap?.detail}</p><div className="mt-6 grid gap-5 lg:grid-cols-2"><section className="rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Set up on this machine</h2><p className="mt-3 text-sm leading-6 text-stone-400">Install Agentia, authenticate using its local setup, and configure the Salesforce checkout and test job IDs. Credentials stay in Agentia; do not paste them here.</p><pre className="mt-4 overflow-auto rounded-lg bg-panel p-4 text-xs leading-7 text-stone-300">npm install -g @copado/agentia-cli@beta{"\n"}agentia setup</pre><p className="mt-3 text-xs leading-5 text-stone-500">See the repository README and .env.example for configuration and current integration limitations.</p><a href="https://developer.copado.com/docs" target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-sm text-accent">Agentia setup documentation <ArrowRight size={14} /></a></section><section className="rounded-xl border border-line p-5"><h2 className="text-sm font-medium">Missing configuration</h2>{cap?.required_configuration.map(name => <p className="mt-3 break-all font-mono text-xs text-stone-400" key={name}>{name}</p>)}{cap?.required_configuration.length === 0 && <p className="mt-3 text-sm text-stone-400">Configuration fields are present. Run the connection checks to verify availability.</p>}<p className="mt-5 text-xs leading-5 text-amber">Live business assertions and environment snapshots still require mappings. A successful generic test job does not certify every business requirement.</p></section></div>
      </section>}
      <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 text-xs text-stone-500"><span className="flex items-center gap-2"><GitBranch size={14} />Evidence has a version. Confidence needs a reason.</span><span>ReleaseProof / 0.3</span></footer>
    </main>
    {detail && <Modal key={detail.id} check={detail} close={() => setDetail(null)} />}
  </div>;
}

