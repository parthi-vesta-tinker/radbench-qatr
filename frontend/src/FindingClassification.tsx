import { useRef, useState } from "react";
import { api, ApiError, describeError } from "./api";
import { useClassification, type ClassificationData } from "./useClassification";
import { StudioDisclosure } from "./StudioDisclosure";
import { LoaderCircle } from "lucide-react";
import type { ClassificationConfig, ClassificationFeedbackInput, ClassificationLabels, ClassificationResource, Review } from "./types";

export const fields = ["finding_group", "certainty", "urgency", "polarity", "temporal_status"] as const;
type Field = keyof ClassificationLabels;
export const names: Record<Field, string> = {
  finding_group: "Finding group", certainty: "Report certainty", urgency: "Communication priority",
  polarity: "Polarity", temporal_status: "Temporal status",
};
export const format = (value: string) => value.replaceAll("_", " ").replace(/^./, char => char.toUpperCase());

export function ResultCard({ run, config, stale }: {run: ClassificationResource; config: ClassificationConfig | null; stale: boolean}) {
  const [action, setAction] = useState<"choose" | "reject" | null>(null);
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
    <details className="jev-inputs">
      <summary>Inputs used</summary>
      <p className="meta">{run.input.source === 'report_excerpts' ? 'Critical finding · Report excerpts + QA comment' : 'Critical finding · QA comment only'}</p>
      {run.input.source === 'report_excerpts' && <><h4>Report excerpts</h4><p className="jev-finding">{run.input.finding_text}</p></>}
      <h4>QA comment</h4><p className="jev-finding">{run.input.qa_comment}</p>
    </details>
    {run.execution_status === "queued" || run.execution_status === "running" ? <span className="jev-loading" role="status" aria-label="Classifying"><LoaderCircle className="journey-spinner" size={16}/></span> : null}
    {run.execution_status === "failed" ? <p className="meta">No classification available.</p> : null}
    {result && <>
      <dl className="jev-labels">{fields.slice(0, 3).map(field => <div key={field}><dt>{names[field]}</dt><dd>{format(result.fields[field]?.label || "Unknown")}</dd></div>)}</dl>
      {canRespond && !action && <div className="jev-actions">
        <button type="button" disabled={busy} onClick={() => {setAction("choose"); setNotice("");}}>Give feedback</button>
      </div>}
      {canRespond && action === "choose" && <div className="jev-actions" role="group" aria-label="Classification feedback">
        <button type="button" disabled={busy} onClick={() => void save({action:"accept"})}>Accept</button>
        <button type="button" disabled={busy} onClick={() => {setLabels(predicted); setAction("reject");}}>Reject / correct</button>
        <button type="button" disabled={busy} onClick={() => setAction(null)}>Cancel</button>
      </div>}
      {canRespond && action === "reject" && labels && <div className="jev-feedback">
        {fields.map(field => <label key={field}>{names[field]}
          <select disabled={busy} value={labels[field]} onChange={event => setLabels({...labels, [field]: event.target.value})}>
            {(config?.labels[field] || [predicted?.[field] || ""]).map(option => <option key={option} value={option}>{format(option)}</option>)}
          </select></label>)}
        <label>Reason (required)<input required disabled={busy} value={reason} maxLength={1000} onChange={event => setReason(event.target.value)} /></label>
        <div className="jev-actions"><button type="button" disabled={!reason.trim() || busy} onClick={() => {
          const changed = fields.some(field => labels[field] !== predicted?.[field]);
          void save(changed ? {action:"edit", final_labels:labels, reason:reason.trim()} : {action:"reject", reason:reason.trim()});
        }}>Save feedback</button>
          <button type="button" disabled={busy} onClick={() => setAction(null)}>Cancel</button></div>
      </div>}
    </>}
    {notice && <p role="status" className="meta">{notice}</p>}
  </article>;
}

export function FindingClassification({review, stale, data, openAnalysis}: {
  review: Review; stale: boolean; data?: ClassificationData; openAnalysis?: () => void;
}) {
  const local = useClassification(review, !data, stale);
  const {runs, config, loading, error} = data ?? local;
  const hasDetails = runs.some(run => run.execution_status === "completed" && run.result);
  const preview = <>
    {loading && !runs.length && <span className="jev-loading" role="status" aria-label="Loading classification"><LoaderCircle className="journey-spinner" size={16}/></span>}
    {!loading && !runs.length && <p className="meta">No classification available.</p>}
    {error && <button type="button" onClick={(data ?? local).refresh}>Retry</button>}
    {runs.slice(0, 2).map((run, index) => <p className="classification-preview" key={run.id}>
      {runs.length > 1 && <span>Finding {index + 1} · </span>}
      {run.execution_status === "completed" && run.result ? <>Group: <strong>{format(run.result.fields.finding_group?.label || "Unknown")}</strong></> :
        run.execution_status === "failed" ? "No classification available." : "Classifying…"}
    </p>)}
    {runs.length > 2 && <p className="meta">+{runs.length - 2} more findings</p>}
  </>;
  return <StudioDisclosure key={`${review.id}:${review.input_version}:${stale}`} title="Classification Overview"
    expandable={hasDetails || runs.length > 2} preview={preview}>
    {openAnalysis && <button type="button" className="linklike" onClick={openAnalysis}>Full analysis</button>}
    {runs.map((run, index) => <div key={run.id} className="jev-observation">
      {runs.length > 1 && <h4>Finding {index + 1}</h4>}
      <ResultCard run={run} config={config} stale={stale}/>
    </div>)}
  </StudioDisclosure>;
}
