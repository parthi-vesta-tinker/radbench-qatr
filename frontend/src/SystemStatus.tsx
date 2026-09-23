import { useEffect, useState, useRef } from "react";
import { X, AlertCircle, Check, Activity, RefreshCw, ChevronDown, ListChecks, CheckCircle2 } from "lucide-react";
import { api, describeError } from "./api";
import { TooltipButton } from "./TooltipButton";
import { StatusPill, tierOf } from "./statusPill";

type Component = { status: string; message: string; code?: string; model?: string; version?: string };
type Health = { status: string; checked_at: string; components: Record<string, Component>; readiness_scope: string };

const LABELS: Record<string, string> = {api:"API backend", database:"Database", dbos:"DBOS", skills:"QA skills", openai:"OpenAI"};

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

  const entries = health ? Object.entries(health.components).map(([name, value]): [string, Component] => [name, name === "openai" && probe ? probe : value]) : [];
  const attention = entries.filter(([, value]) => tierOf(value.status) !== "neutral");
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
        <div className="health-heading-copy">
          <h3>Service health</h3>
          <p className={"health-verdict " + verdictTier} role="status">{verdictTier === "neutral" && !failure ? <Check size={14}/> : <AlertCircle size={14}/>}{checking ? "Checking…" : failure ? "Unavailable" : configurationError ? "Needs attention" : verdict ?? "Not checked"}</p>
        </div>
        <div className="health-refresh">
          <TooltipButton className="icon-button primary" side="left" label="Refresh status" disabled={checking || probing}
            onClick={() => { setProbe(null); setRefresh(n => n + 1); retryConfiguration(); }}>
            <RefreshCw size={17} className={checking ? "journey-spinner" : undefined}/>
          </TooltipButton>
          <span className="meta">{health ? <>Last checked<br/><time dateTime={health.checked_at}>{new Date(health.checked_at).toLocaleTimeString()}</time></> : "Not checked"}</span>
        </div>
        <TooltipButton className="icon-button health-close" side="left" label="Close service health" onClick={() => close(true)}><X size={16}/></TooltipButton>
      </div>
      {configurationError && <p className="error">Configuration needs attention.</p>}
      {failure && <p className="error" role="alert">{failure}</p>}
      {entries.length > 0 && <details className="health-checks">
        <summary><ListChecks size={16}/><span>View all {entries.length} checks</span><ChevronDown size={16} className="health-chevron"/></summary>
        <dl className="health-check-list">{entries.map(([name, value]) => <div className="health-check-row" key={name}>
          <dt>{LABELS[name] ?? name}</dt>
          <dd><StatusPill status={name === "openai" && probing ? "checking" : value.status}/>
            {name === "openai" && <TooltipButton className="icon-button" side="left" label={probing ? "Checking OpenAI connection" : "Check OpenAI connection"}
              disabled={probing || checking || health?.components.openai?.status !== "configured"} onClick={() => void checkOpenAI()}>
              {probing ? <RefreshCw size={16} className="journey-spinner"/> : <CheckCircle2 size={16}/>}
            </TooltipButton>}
          </dd>
        </div>)}</dl>
        {probe && <p className="health-probe-result meta" role="status">{tierOf(probe.status) === "neutral" ? "OpenAI connection checked." : <>{probe.message}{probe.code && <> · <code>{probe.code}</code></>}</>}</p>}
      </details>}
    </div>
  </div>;
}
