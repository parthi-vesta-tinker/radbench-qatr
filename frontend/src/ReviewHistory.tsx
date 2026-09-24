import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import type { FeedbackRecord, ReviewComments, ReviewSummary } from './types';

type Modal =
  | { kind: 'comments'; row: ReviewSummary; data: ReviewComments }
  | { kind: 'feedback'; row: ReviewSummary; data: FeedbackRecord[] }
  | null;
type QuickRange = 'all' | '24h' | '3d' | '7d' | 'custom';

function rangeStart(range: Exclude<QuickRange, 'all' | 'custom'>) {
  const hours = range === '24h' ? 24 : range === '3d' ? 72 : 168;
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

function displayTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function historyStatus(status: string) {
  return status.replaceAll('_', ' ').replace(/^./, letter => letter.toUpperCase());
}

function CommentDialog({ modal, close }: { modal: Exclude<Modal, null>; close: () => void }) {
  const comments = modal.kind === 'comments' ? modal.data : null;
  const feedback = modal.kind === 'feedback' ? modal.data : null;
  return <div className="history-modal-backdrop" role="presentation" onMouseDown={close}>
    <section className="history-modal" role="dialog" aria-modal="true" aria-labelledby="history-modal-title" onMouseDown={event => event.stopPropagation()}>
      <div className="history-modal-heading">
        <div><h2 id="history-modal-title">{modal.kind === 'comments' ? 'PACS comments' : 'Feedback'}</h2><p className="meta">Review {modal.row.display_id}</p></div>
        <button type="button" onClick={close} aria-label="Close history dialog">Close</button>
      </div>
      {comments && <>
        {comments.execution_status !== 'completed' && <p className="meta">Comments are available after the review is completed.</p>}
        {comments.execution_status === 'completed' && !comments.general_comments?.length && !comments.critical_comments?.length && <p className="meta">No comments were produced for this review.</p>}
        {!!comments.general_comments?.length && <section className="history-comment-group"><h3>PACS comments</h3><ol>{comments.general_comments.map(comment => <li key={comment.observation_id}>{comment.comment}</li>)}</ol></section>}
        {!!comments.critical_comments?.length && <section className="history-comment-group"><h3>Critical findings</h3><ol>{comments.critical_comments.map(comment => <li key={comment.observation_id}>{comment.comment}</li>)}</ol></section>}
      </>}
      {feedback && (feedback.length ? <ol className="history-feedback-list">{feedback.map(item => <li key={item.id}><strong>{item.rating === 'up' ? 'Accepted' : 'Needs review'}</strong><span>{item.reason?.replaceAll('_', ' ') ?? 'No reason recorded'}</span>{item.explanation && <p>{item.explanation}</p>}<time dateTime={item.created_at}>{displayTime(item.created_at)}</time></li>)}</ol> : <p className="meta">No feedback has been recorded for this review.</p>)}
    </section>
  </div>;
}

export function ReviewHistory({ busy, openReview, refreshToken = 0 }: { busy: boolean; openReview: (id: string) => void; refreshToken?: number }) {
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [result, setResult] = useState('');
  const [feedback, setFeedback] = useState('');
  const [quickRange, setQuickRange] = useState<QuickRange>('all');
  const [submittedAfter, setSubmittedAfter] = useState('');
  const [submittedBefore, setSubmittedBefore] = useState('');
  const [rows, setRows] = useState<ReviewSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [after, setAfter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [modal, setModal] = useState<Modal>(null);

  useEffect(() => {
    let stopped = false;
    setLoading(true); setError('');
    const params = new URLSearchParams({ limit: '20' });
    if (query) params.set('q', query);
    if (status) params.set('status', status);
    if (result === 'critical') params.set('critical', 'true');
    else if (result) params.set('outcome', result);
    if (feedback) params.set('has_feedback', feedback);
    if (submittedAfter) params.set('submitted_after', submittedAfter);
    if (submittedBefore) params.set('submitted_before', submittedBefore);
    if (after) params.set('starting_after', after);
    api.history(params.toString()).then(page => {
      if (!stopped) { setRows(old => after ? [...old, ...page.items] : page.items); setCursor(page.next_cursor); }
    }).catch(e => { if (!stopped) setError(describeError(e)); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [query, status, result, feedback, submittedAfter, submittedBefore, after, refresh, refreshToken]);

  function reset() { setAfter(''); setRows([]); setCursor(null); }
  function applyFilters(change: () => void) { reset(); change(); }
  function chooseRange(next: QuickRange) {
    applyFilters(() => {
      setQuickRange(next);
      if (next === 'all') { setSubmittedAfter(''); setSubmittedBefore(''); }
      else if (next !== 'custom') { setSubmittedAfter(rangeStart(next)); setSubmittedBefore(''); }
    });
  }
  async function openComments(row: ReviewSummary) {
    try { setModal({ kind: 'comments', row, data: await api.comments(row.id) }); }
    catch (e) { setError(describeError(e)); }
  }
  async function openFeedback(row: ReviewSummary) {
    try { setModal({ kind: 'feedback', row, data: (await api.feedbackHistory(row.id)).items }); }
    catch (e) { setError(describeError(e)); }
  }

  return <main className="history-pane">
    <div className="section-heading"><div><h1>Review history</h1><p className="meta">Latest submitted reviews, comments, and recorded feedback.</p></div></div>
    <form className="history-filters" onSubmit={event => { event.preventDefault(); applyFilters(() => { setQuery(search.trim()); setRefresh(value => value + 1); }); }}>
      <label>Search reports<input type="search" value={search} maxLength={200} onChange={event => setSearch(event.target.value)} placeholder="Report text or review ID" /></label>
      <button type="submit">Search</button>
      <label>Status<select value={status} onChange={event => applyFilters(() => setStatus(event.target.value))}><option value="">All statuses</option><option value="completed">Completed</option><option value="running">Running</option><option value="queued">Queued</option><option value="needs_input">Input needed</option><option value="failed">Failed</option></select></label>
      <label>Result<select value={result} onChange={event => applyFilters(() => setResult(event.target.value))}><option value="">All results</option><option value="critical">Critical comments</option><option value="observations">With comments</option><option value="no_observations">No comments</option></select></label>
      <label>Feedback<select value={feedback} onChange={event => applyFilters(() => setFeedback(event.target.value))}><option value="">Any feedback status</option><option value="true">Feedback recorded</option><option value="false">No feedback yet</option></select></label>
      <label>Submitted<select aria-label="Submitted time range" value={quickRange} onChange={event => chooseRange(event.target.value as QuickRange)}><option value="all">Any time</option><option value="24h">Last 24 hours</option><option value="3d">Last 3 days</option><option value="7d">Last 7 days</option><option value="custom">Custom range</option></select></label>
      {quickRange === 'custom' && <span className="history-custom-range"><label>From<input aria-label="Submitted after" type="datetime-local" value={submittedAfter ? submittedAfter.slice(0, 16) : ''} onChange={event => applyFilters(() => setSubmittedAfter(event.target.value ? new Date(event.target.value).toISOString() : ''))} /></label><label>To<input aria-label="Submitted before" type="datetime-local" value={submittedBefore ? submittedBefore.slice(0, 16) : ''} onChange={event => applyFilters(() => setSubmittedBefore(event.target.value ? new Date(event.target.value).toISOString() : ''))} /></label></span>}
    </form>
    {error && <p className="error" role="alert">{error} <button onClick={() => setRefresh(value => value + 1)}>Retry history</button></p>}
    <div className="history-table review-history-table" role="region" aria-label="Saved reviews" tabIndex={0}><table><thead><tr><th>Review ID</th><th>Report description</th><th>Submitted by</th><th>Submitted time</th><th>Status</th><th>Comments</th><th>Feedback</th></tr></thead><tbody>{rows.map(row => <tr key={row.id}>
      <td data-label="Review ID"><button className="report-link review-short-id" disabled={busy || loading} onClick={() => openReview(row.id)}>{row.display_id}</button><span className="meta">{row.mode === 'demo' ? 'Demo' : 'AI'}</span></td>
      <td data-label="Report description"><button className="report-link history-description" title={row.preview} disabled={busy || loading} onClick={() => openReview(row.id)}>{row.preview || 'Open report'}</button></td>
      <td data-label="Submitted by">{row.submitted_by ?? <span className="meta">Not recorded</span>}</td>
      <td data-label="Submitted time"><time dateTime={row.created_at}>{displayTime(row.created_at)}</time></td>
      <td data-label="Status"><span className="history-status">{historyStatus(row.execution_status)}</span></td>
      <td data-label="Comments">{row.execution_status === 'completed' ? <button className="linklike" onClick={() => void openComments(row)}>{row.general_count || row.critical_count ? `${row.general_count} PACS · ${row.critical_count} critical` : 'No comments'}</button> : '—'}</td>
      <td data-label="Feedback">{row.feedback_count === null ? '—' : <button className="linklike" onClick={() => void openFeedback(row)}>{row.feedback_count ? `${row.feedback_count} recorded` : 'No feedback'}</button>}</td>
    </tr>)}</tbody></table></div>
    {loading && <p className="meta" role="status">Loading reviews…</p>}
    {!loading && !error && !rows.length && <div className="empty">No reviews match these filters.</div>}
    {cursor && <button disabled={loading} onClick={() => setAfter(cursor)}>Load more reviews</button>}
    {busy && <p className="meta">Wait for the current review to finish before opening another report.</p>}
    {modal && <CommentDialog modal={modal} close={() => setModal(null)} />}
  </main>;
}
