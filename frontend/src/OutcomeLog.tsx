import { useEffect, useRef, useState } from 'react';
import { api, ApiError, describeError } from './api';
import type { OutcomeInput, OutcomeRecord } from './types';

export const stakeholderLabel = (value: string) => ({ qa: 'QA', radiologist: 'Radiologist', facility: 'Facility' }[value] ?? value);
export const decisionLabel = (value: string) => ({ accepted: 'Accepted', rejected: 'Rejected', review_requested: 'Review requested', unknown: 'Unknown / withdrawn' }[value] ?? value);

export function OutcomeLog({ reviewId, resultVersion, disabled }: { reviewId: string; resultVersion: number; disabled: boolean }) {
  const [open, setOpen] = useState(false);
  const [payload, setPayload] = useState<OutcomeInput>({ result_version: resultVersion, stakeholder: 'qa', subject: 'report', decision: 'review_requested', source_note: '' });
  const [rows, setRows] = useState<OutcomeRecord[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [after, setAfter] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [retry, setRetry] = useState(false);
  const [error, setError] = useState('');
  const [historyError, setHistoryError] = useState('');
  const [message, setMessage] = useState('');
  const pending = useRef<{ payload: OutcomeInput; key: string } | null>(null);
  useEffect(() => {
    if (!open) return;
    let stopped = false;
    setLoading(true); setHistoryError('');
    api.outcomes(reviewId, after || undefined).then(page => {
      if (!stopped) { setRows(old => after ? [...new Map([...old, ...page.items].map(r => [r.outcome_id, r])).values()] : page.items); setCursor(page.next_cursor); }
    }).catch(e => { if (!stopped) setHistoryError(describeError(e)); }).finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [open, reviewId, attempt, after]);
  async function save() {
    if (disabled || saving || !payload.source_note.trim()) return;
    pending.current ??= { payload: { ...payload, source_note: payload.source_note.trim() }, key: crypto.randomUUID() };
    setSaving(true); setError(''); setMessage('');
    try {
      await api.saveOutcome(reviewId, pending.current.payload, pending.current.key);
      pending.current = null; setRetry(false); setPayload(old => ({ ...old, source_note: '' }));
      setAfter(''); setAttempt(n => n + 1); setMessage('Outcome recorded. Original report and QA comments are unchanged.');
    } catch (e) {
      // A malformed success response may follow a committed outcome, just like a timeout.
      const uncertain = !(e instanceof ApiError) || e.status < 400 || e.status >= 500;
      if (!uncertain) pending.current = null;
      setRetry(uncertain); setError(describeError(e));
    } finally { setSaving(false); }
  }
  return <details className="disclosure disclosure-section outcome-log" open={open} onToggle={e => setOpen(e.currentTarget.open)}>
    <summary>Stakeholder outcomes</summary>
    <p className="meta">Record a decision from QA, the radiologist, or the facility. Operator-recorded—not a verified signature, delivery receipt, or clinical adjudication.</p>
    <form onSubmit={e => { e.preventDefault(); void save(); }}>
      <fieldset disabled={disabled || saving || retry}>
        <div className="history-filters">
          <label>Perspective<select value={payload.stakeholder} onChange={e => setPayload(old => ({ ...old, stakeholder: e.target.value as OutcomeInput['stakeholder'] }))}><option value="qa">QA</option><option value="radiologist">Radiologist</option><option value="facility">Facility</option></select></label>
          <label>Decision about<select value={payload.subject} onChange={e => setPayload(old => ({ ...old, subject: e.target.value as OutcomeInput['subject'] }))}><option value="report">Report</option><option value="qa_comments">QA comments</option></select></label>
          <label>Decision<select value={payload.decision} onChange={e => setPayload(old => ({ ...old, decision: e.target.value as OutcomeInput['decision'] }))}><option value="review_requested">Review requested</option><option value="accepted">Accepted</option><option value="rejected">Rejected</option><option value="unknown">Unknown / withdraw previous decision</option></select></label>
        </div>
        <label htmlFor="outcome-source">Source / reason <span className="required">Required</span></label>
        <textarea id="outcome-source" rows={2} maxLength={2000} value={payload.source_note} onChange={e => setPayload(old => ({ ...old, source_note: e.target.value }))} placeholder="Reference the decision or explain the requested review. Avoid unnecessary patient identifiers." required />
      </fieldset>
      <button disabled={disabled || saving || !payload.source_note.trim()}>{saving ? 'Recording…' : retry ? 'Retry same outcome' : 'Record outcome'}</button>
    </form>
    {retry && <p className="meta">Confirmation was lost. Retry uses the same operation; do not record a second outcome.</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {message && <p className="meta" role="status">{message}</p>}
    {historyError && <p className="error" role="alert">{historyError} <button onClick={() => setAttempt(n => n + 1)}>Retry outcome history</button></p>}
    {loading && <p className="meta" role="status">Loading outcomes…</p>}
    <ol>{rows.map(row => <li key={row.outcome_id}><strong>{stakeholderLabel(row.stakeholder)} · {row.subject === 'report' ? 'Report' : 'QA comments'} · {decisionLabel(row.decision)}</strong><p>{row.source_note}</p><p className="meta"><time dateTime={row.created_at}>{new Date(row.created_at).toLocaleString()}</time> · Result v{row.result_version} · Operator-recorded</p></li>)}</ol>
    {!loading && !historyError && !rows.length && <p className="meta">No outcomes recorded.</p>}
    {cursor && <button disabled={loading} onClick={() => setAfter(cursor)}>Load more outcomes</button>}
    <p className="meta">Latest entry per perspective and subject is counted. Earlier entries remain in history.</p>
  </details>;
}
