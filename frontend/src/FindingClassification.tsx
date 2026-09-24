import { useEffect, useRef, useState } from "react";
import { api, ApiError, describeError } from "./api";
import type { ClassificationConfig, ClassificationFeedbackInput, ClassificationLabels, ClassificationResource, Review } from "./types";

const fields = ["finding_group", "certainty", "urgency", "polarity", "temporal_status"] as const;
type Field = keyof ClassificationLabels;
const names: Record<Field, string> = {
  finding_group: "Finding group", certainty: "Report certainty", urgency: "Suggested communication priority",
  polarity: "Polarity", temporal_status: "Temporal status",
};
const format = (value: string) => value.replaceAll("_", " ").replace(/^./, char => char.toUpperCase());

function ResultCard({ run, config, stale }: {run: ClassificationResource; config: ClassificationConfig; stale: boolean}) {
  const [action, setAction] = useState<"edit" | "reject" | null>(null);
  const [labels, setLabels] = useState<ClassificationLabels | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const pending = useRef<{signature:string; key:string} | null>(null);
  const result = run.result;
  const predicted = result ? Object.fromEntries(fields.map(field => [field, result.fields[field]?.label])) as ClassificationLabels : null;
  const canRespond = !stale && run.source_status === "current" && run.execution_status === "completed" && Boolean(result);

  async function save(payload: ClassificationFeedbackInput) {
    if (!canRespond || busy) return;
    const signature = JSON.stringify(payload);
    if (pending.current?.signature !== signature) pending.current = {signature, key: crypto.randomUUID()};
    setBusy(true); setNotice("");
    try {
      await api.classificationFeedback(run.id, payload, pending.current.key);
      pending.current = null; setAction(null); setReason("");
      setNotice(payload.action === "accept" ? "Labels accepted." : payload.action === "edit" ? "Correction saved." : "Suggestion rejected.");
    } catch (error) {
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) pending.current = null;
      setNotice(describeError(error));
    } finally { setBusy(false); }
  }

  return <article className="jev-card">
    <p className="jev-finding">{run.input.finding_text}</p>
    {run.execution_status === "queued" || run.execution_status === "running" ? <p className="meta" role="status">Classifying…</p> : null}
    {run.execution_status === "failed" ? <p className="notice" role="alert">{run.error?.message || "Classification could not finish."}</p> : null}
    {result && <>
      <dl className="jev-labels">{fields.slice(0, 3).map(field => <div key={field}><dt>{names[field]}</dt><dd>{format(result.fields[field]?.label || "Unknown")}</dd></div>)}</dl>
      {result.fields.urgency?.label !== "cannot_determine" && <p className="meta">Verify the suggested communication priority against the report and local policy.</p>}
      <p className="meta">Model suggestion · {result.calibration_status === "uncalibrated" ? "Uncalibrated" : "Research calibration"} · Review all labels.</p>
      <details className="jev-details"><summary>Classification details</summary>
        <dl>{fields.slice(3).map(field => <div key={field}><dt>{names[field]}</dt><dd>{format(result.fields[field]?.label || "Unknown")}</dd></div>)}</dl>
        {fields.map(field => <div key={field} className="jev-distribution"><strong>{names[field]}</strong>
          <p className="meta">Raw model probability · {Math.round((result.fields[field]?.top_probability || 0) * 100)}% top · {Math.round((result.fields[field]?.margin || 0) * 100)}% margin · provider confidence {Math.round((result.fields[field]?.provider_confidence || 0) * 100)}%</p>
          <ul>{Object.entries(result.fields[field]?.raw_probabilities || {}).map(([label, probability]) => <li key={label}>{format(label)}: {(probability * 100).toFixed(1)}%</li>)}</ul>
          {result.fields[field]?.review_reasons?.map(text => <p className="meta" key={text}>{text}</p>)}
        </div>)}
        <p className="meta">Model {run.provenance.model} · Rubric {run.provenance.rubric_id} · {result.calibrator_id || "No fitted calibrator"}</p>
      </details>
      {canRespond && <div className="jev-actions">
        <button type="button" disabled={busy} onClick={() => void save({action:"accept"})}>Accept labels</button>
        <button type="button" disabled={busy} onClick={() => {setLabels(predicted); setAction("edit"); setNotice("");}}>Edit labels</button>
        <button type="button" disabled={busy} onClick={() => {setAction("reject"); setNotice("");}}>Reject suggestion</button>
      </div>}
      {canRespond && action && <div className="jev-feedback">
        {action === "edit" && labels && fields.map(field => <label key={field}>{names[field]}
          <select value={labels[field]} onChange={event => setLabels({...labels, [field]: event.target.value})}>
            {(config.labels[field] || []).map(option => <option key={option} value={option}>{format(option)}</option>)}
          </select></label>)}
        <label>Reason<input value={reason} maxLength={1000} onChange={event => setReason(event.target.value)} /></label>
        <div className="jev-actions"><button type="button" disabled={!reason.trim() || busy} onClick={() => void save(action === "edit" ? {action, final_labels: labels, reason} : {action, reason})}>Save</button>
          <button type="button" onClick={() => setAction(null)}>Cancel</button></div>
      </div>}
    </>}
    {notice && <p role="status" className="meta">{notice}</p>}
  </article>;
}

export function FindingClassification({review, stale}: {review: Review; stale: boolean}) {
  const [config, setConfig] = useState<ClassificationConfig | null>(null);
  const [runs, setRuns] = useState<ClassificationResource[]>([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState("");
  const pending = useRef<Record<string, string>>({});
  const source = `${review.id}:${review.input_version}`;
  useEffect(() => {
    let cancelled = false;
    api.classificationConfig().then(value => { if (!cancelled) setConfig(value); })
      .catch(cause => {if (!cancelled) setError(describeError(cause));});
    return () => {cancelled = true;};
  }, []);
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    let polls = 0;
    setRuns([]); setError("");
    async function poll() {
      try {
        const values = await api.classificationsForReview(review.id);
        if (cancelled) return;
        setRuns(values.filter(value => value.input_version === review.input_version));
        const awaiting = review.result?.critical_comments.some(observation =>
          !values.some(value => value.observation_id === observation.observation_id
            && (value.execution_status === "completed" || value.execution_status === "failed")));
        if (awaiting && ++polls < 60) timer = setTimeout(poll, 1000);
      } catch (cause) { if (!cancelled) setError(describeError(cause)); }
    }
    void poll();
    return () => {cancelled = true; clearTimeout(timer);};
  }, [source, review.id, review.input_version]);
  async function classify(observationId: string) {
    if (!config?.ready || stale || busyId) return;
    const key = pending.current[observationId] ||= crypto.randomUUID();
    setBusyId(observationId); setError("");
    try {
      const run = await api.classify({review_id: review.id, input_version: review.input_version, observation_id: observationId}, key);
      delete pending.current[observationId];
      setRuns(old => [...old.filter(item => item.id !== run.id), run]);
      let current = run;
      while (current.execution_status === "queued" || current.execution_status === "running") {
        await new Promise(resolve => setTimeout(resolve, 1000));
        current = await api.classification(run.id);
        setRuns(old => old.map(item => item.id === run.id ? current : item));
      }
    } catch (cause) {
      if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) delete pending.current[observationId];
      setError(describeError(cause));
    } finally { setBusyId(""); }
  }
  return <section className="studio-section jev-section" aria-label="Finding classification">
    <h3>Finding classification</h3>
    <p className="meta">JEV suggests labels for critical findings in this completed review. A radiologist reviews every label.</p>
    {!config?.ready && <p className="meta">{config?.reason || "Checking JEV availability…"}</p>}
    {error && <p className="notice" role="alert">{error}</p>}
    {review.result?.critical_comments.map(observation => {
      const matching = runs.filter(run => run.observation_id === observation.observation_id);
      const latest = matching.at(-1);
      return <div className="jev-observation" key={observation.observation_id}>
        <p>{observation.comment}</p>
        {latest && config ? <ResultCard key={latest.id} run={latest} config={config} stale={stale}/> : null}
        {(!latest || latest.execution_status === "failed") && config?.ready && <button type="button" disabled={stale || Boolean(busyId)} onClick={() => void classify(observation.observation_id)}>
          {busyId === observation.observation_id ? "Starting…" : latest ? "Try as new request" : "Classify finding"}
        </button>}
      </div>;
    })}
  </section>;
}
