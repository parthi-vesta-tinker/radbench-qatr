import { useEffect, useState, useRef } from "react";
import { X, AlertCircle, Check, Activity } from "lucide-react";
import { api, describeError } from "./api";
import { TooltipButton } from "./TooltipButton";
import { StatusPill, tierOf } from "./statusPill";

type Component = { status: string; message: string; code?: string; model?: string; version?: string };
type Health = { status: string; checked_at: string; components: Record<string, Component>; readiness_scope: string };

const LABELS: Record<string, string> = {api:"API backend", database:"Database", dbos:"DBOS", skills:"QA skills", openai:"OpenAI"};
function Rows({ entries }: { entries: [string, Component][] }) {
  return <dl>{entries.map(([name, value]) => <div key={name}>
    <dt>{LABELS[name] ?? name} <StatusPill status={value.status}/></dt>
    <dd>{value.message}{value.code && <code>{value.code}</code>}</dd>
  </div>)}</dl>;
}

export function SystemStatus({ configurationError, retryConfiguration }: { configurationError: string; retryConfiguration: () => void }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [failure, setFailure] = useState("");
  const [checking, setChecking] = useState(false);
  const [probe, setProbe] = useState<Component | null>(null);
  const [probing, setProbing] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let stopped = false;
    setChecking(true);
    api.status().then(value => { if (!stopped) { setHealth(value); setFailure(""); } })
      .catch(error => { if (!stopped) { setHealth(null); setFailure(describeError(error)); } })
      .finally(() => { if (!stopped) setChecking(false); });
    return () => { stopped = true; };
  }, [refresh]);
  async function checkOpenAI() {
    setProbing(true);
    try { setProbe(await api.checkOpenAI()); }
    catch (error) { setProbe({ status: "error", message: describeError(error) }); }
    finally { setProbing(false); }
  }
  const panel = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const openRef = useRef(false);
  openRef.current = open;
  function close(restoreFocus: boolean) {
    if (!panel.current) return;
    setOpen(false);
    // Focus returns for deliberate dismissal only; an outside click belongs to whatever was clicked.
    if (restoreFocus) panel.current.querySelector<HTMLButtonElement>(".health-trigger")?.focus();
  }
  useEffect(() => {
    const isOpen = () => openRef.current;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape" && isOpen()) close(true); };
    const onPointer = (event: PointerEvent) => {
      if (isOpen() && panel.current && !panel.current.contains(event.target as Node)) close(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => { document.removeEventListener("keydown", onKey); document.removeEventListener("pointerdown", onPointer); };
  }, []);

  const entries = health ? Object.entries(health.components) : [];
  const attention = entries.filter(([, value]) => tierOf(value.status) !== "neutral");
  const passing = entries.filter(([, value]) => tierOf(value.status) === "neutral");
  const summaryLabel = checking ? "Checking…" : failure ? "Unavailable" : configurationError ? "Needs attention"
    : !health ? "Not checked" : health.status === "ready" && !attention.length ? "Local checks passed" : "Needs attention";
  const verdict = !health ? null : attention.length
    ? `${attention.length} of ${entries.length} checks need attention`
    : `All ${entries.length} checks passed`;
  const verdictTier = attention.length ? (attention.some(([, v]) => tierOf(v.status) === "danger") ? "danger" : "attention") : "neutral";

  return <div ref={panel} className="system-status">
    <TooltipButton className="icon-button health-trigger" side="bottom" label={`Service health: ${summaryLabel}`}
      aria-expanded={open} aria-controls="service-health-panel" onClick={() => setOpen(value => !value)}>
      <Activity size={19} aria-hidden="true"/><span className={"status-dot " + (failure ? "danger" : configurationError ? "attention" : verdictTier)} aria-hidden="true"/>
    </TooltipButton>
    <div id="service-health-panel" className="health-panel" hidden={!open} role="dialog" aria-label="Service health">
      <div className="health-panel-heading">
        <h3>Service health</h3>
        <button type="button" className="icon-button" aria-label="Close service health" onClick={() => close(true)}><X size={16}/></button>
      </div>
      {verdict && <p className={"health-verdict " + verdictTier}>{verdictTier === "neutral" ? <Check size={15}/> : <AlertCircle size={15}/>}{verdict}</p>}
      <p className="meta">{health ? `Last checked ${new Date(health.checked_at).toLocaleTimeString()} · ` : ""}Local checks do not verify model inference.</p>
      {configurationError && <p className="error">Configuration needs attention.</p>}
      {failure && <p className="error" role="status">{failure}</p>}
      {attention.length > 0 && <Rows entries={attention}/>}
      {passing.length > 0 && (attention.length > 0
        ? <details className="disclosure disclosure-aside health-passing"><summary>{passing.length} passing {passing.length === 1 ? "check" : "checks"}</summary><Rows entries={passing}/></details>
        : <details className="disclosure disclosure-aside health-passing"><summary>View all {passing.length} checks</summary><Rows entries={passing}/></details>)}
      <div className="status-actions">
        <button type="button" disabled={checking || probing} onClick={() => { setProbe(null); setRefresh(n => n + 1); retryConfiguration(); }}>Refresh status</button>
        <button type="button" disabled={probing || checking || health?.components.openai?.status !== "configured"} onClick={() => void checkOpenAI()}>{probing ? "Checking OpenAI…" : "Check OpenAI connection"}</button>
      </div>
      {probe && <p role="status">{probe.message}{probe.code && <code>{probe.code}</code>}</p>}
      <p className="meta">OpenAI check reads model metadata only. It sends no report and does not run a paid review.</p>
    </div>
  </div>;
}
