import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import type { ReviewSummary } from './types';
import { StatusPill } from './statusPill';
export function ReviewHistory({busy, openReview}: {busy:boolean; openReview:(id:string)=>void}) {
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [result, setResult] = useState('');
  const [feedback, setFeedback] = useState('');
  const [rows, setRows] = useState<ReviewSummary[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [after, setAfter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let stopped = false;
    setLoading(true); setError('');
    const params = new URLSearchParams({limit:'20'});
    if (query) params.set('q', query);
    if (status) params.set('status',status);
    if (result === 'critical') params.set('critical','true');
    else if (result) params.set('outcome',result);
    if (feedback) params.set('has_feedback',feedback);
    if (after) params.set('starting_after',after);
    api.history(params.toString()).then(page => {
      if (!stopped) { setRows(old => after ? [...old,...page.items] : page.items); setCursor(page.next_cursor); }
    }).catch(e => { if (!stopped) setError(describeError(e)); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [query,status,result,feedback,after,refresh]);
  function reset() {setAfter(''); setRows([]); setCursor(null);}
  return <main className="history-pane">
    <div className="section-heading"><div><h1>Review history</h1><p className="meta">Saved reports, QA comments and feedback</p></div><button disabled={loading} onClick={() => {reset();setRefresh(n=>n+1);}}>Refresh</button></div>
    <form className="history-filters" onSubmit={e => {e.preventDefault();reset();setQuery(search.trim());setRefresh(n=>n+1);}}>
      <label>Search reports<input type="search" value={search} maxLength={200} onChange={e=>setSearch(e.target.value)} placeholder="Report text or review ID"/></label>
      <button type="submit">Search</button>
      <label>Status<select value={status} onChange={e=>{reset();setStatus(e.target.value);}}><option value="">All statuses</option><option value="completed">Completed</option><option value="running">Running</option><option value="queued">Queued</option><option value="needs_input">Input needed</option><option value="failed">Failed</option></select></label>
      <label>Result<select value={result} onChange={e=>{reset();setResult(e.target.value);}}><option value="">All results</option><option value="critical">Critical comments</option><option value="observations">With comments</option><option value="no_observations">No comments</option></select></label>
      <label>Feedback<select value={feedback} onChange={e=>{reset();setFeedback(e.target.value);}}><option value="">Any feedback status</option><option value="true">Feedback recorded</option><option value="false">No feedback yet</option></select></label>
    </form>
    {error && <p className="error" role="alert">{error} <button onClick={()=>setRefresh(n=>n+1)}>Retry history</button></p>}
    <div className="history-table review-history-table" role="region" aria-label="Saved reviews" tabIndex={0}><table><thead><tr><th>Report</th><th>Last submitted</th><th>Status</th><th>Comments</th><th>Feedback</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}>
      <td data-label="Report"><button className="report-link" disabled={busy || loading} onClick={()=>openReview(row.id)}>{row.preview || row.id}</button><div className="meta review-id">{row.id} · {row.mode === 'demo' ? 'Demo' : 'AI'}</div></td>
      <td data-label="Last submitted"><time dateTime={row.created_at}>{new Date(row.created_at).toLocaleString()}</time></td>
      <td data-label="Status"><StatusPill status={row.execution_status}/></td><td data-label="Comments">{row.execution_status !== 'completed' ? '—' : row.outcome === 'no_observations' ? 'None' : `${row.general_count} general · ${row.critical_count} critical`}</td><td data-label="Feedback">{row.feedback_count ?? '—'}</td>
    </tr>)}</tbody></table></div>
    {loading && <p className="meta" role="status">Loading reviews…</p>}
    {!loading && !error && !rows.length && <div className="empty">No reviews match these filters.</div>}
    {cursor && <button disabled={loading} onClick={()=>setAfter(cursor)}>Load more reviews</button>}
    {busy && <p className="meta">Wait for the current review to finish before opening another report.</p>}
  </main>;
}
