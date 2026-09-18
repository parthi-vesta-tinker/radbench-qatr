import { useEffect, useState, useRef } from "react";
import { api, describeError } from "./api";

type Component = { status: string; message: string; code?: string; model?: string; version?: string };
type Health = { status: string; checked_at: string; components: Record<string, Component>; readiness_scope: string };
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
  const panel = useRef<HTMLDetailsElement>(null);
  return <details ref={panel} className="system-status" onKeyDown={e => { if(e.key === "Escape" && panel.current) { panel.current.open = false; panel.current.querySelector("summary")?.focus(); } }}>
    <summary onDoubleClick={() => { if(panel.current) panel.current.open = true; }}>Health · {checking ? "Checking…" : failure ? "Unavailable" : configurationError ? "Needs attention" : !health ? "Not checked" : health.status === "ready" ? "Local checks passed" : "Needs attention"}</summary>
    <div className="health-panel"><h3>Service health</h3>
    {configurationError && <p className="error">Configuration needs attention.</p>}
    <p className="meta">Local checks do not verify model inference.</p>
    {failure && <p className="error" role="status">{failure}</p>}
    {health && <dl>{Object.entries(health.components).map(([name, value]) => <div key={name}>
      <dt>{({api:"API backend", database:"Database", dbos:"DBOS", skills:"QA skills", openai:"OpenAI"} as Record<string,string>)[name] ?? name} <span className="meta">{value.status.replaceAll("_", " ")}</span></dt>
      <dd>{value.message}{value.code && <code>{value.code}</code>}</dd>
    </div>)}</dl>}
    <div className="status-actions">
      <button type="button" disabled={checking || probing} onClick={() => { setProbe(null); setRefresh(n => n + 1); retryConfiguration(); }}>Refresh status</button>
      <button type="button" disabled={probing || checking || health?.components.openai?.status !== "configured"} onClick={() => void checkOpenAI()}>{probing ? "Checking OpenAI…" : "Check OpenAI connection"}</button>
    </div>
    {probe && <p role="status">{probe.message}{probe.code && <code>{probe.code}</code>}</p>}
    <p className="meta">OpenAI check reads model metadata only. It sends no report and does not run a paid review.</p>
    {health && <p className="meta">Last checked: {new Date(health.checked_at).toLocaleTimeString()}</p>}
    </div>
  </details>;
}
