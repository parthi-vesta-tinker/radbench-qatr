import { useEffect, useState } from 'react';
import { ThumbsDown, ThumbsUp } from 'lucide-react';
import { api, describeError } from './api';
import { feedbackReasons, reasonLabel } from './feedbackLabels';
import type { FeedbackInboxItem } from './types';

export function FeedbackInbox({ openReview }: { openReview: (id: string) => void }) {
  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState({ q: '', rating: 'down', reason: '', source: 'openai' });
  const [after, setAfter] = useState('');
  const [refresh, setRefresh] = useState(0);
  const [rows, setRows] = useState<FeedbackInboxItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let stopped = false;
    setLoading(true); setError('');
    const params = new URLSearchParams({ limit: '20', source: filters.source });
    for (const field of ['q', 'rating', 'reason'] as const) if (filters[field]) params.set(field, filters[field]);
    if (after) params.set('starting_after', after);
    api.feedbackInbox(params.toString()).then(page => {
      if (!stopped) {
        setRows(old => after ? [...new Map([...old, ...page.items].map(row => [row.feedback.id, row])).values()] : page.items);
        setCursor(page.next_cursor);
      }
    }).catch(e => { if (!stopped) setError(describeError(e)); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [filters, after, refresh]);
  function reset() { setAfter(''); setRows([]); setCursor(null); }
  function filter(field: keyof typeof filters, value: string) {
    reset(); setFilters(old => ({ ...old, [field]: value }));
  }
  return <main className="history-pane feedback-inbox">
    <div className="section-heading"><div><h1>Feedbacks</h1><p className="meta">Saved feedback across reports · Newest first</p></div>
      <button disabled={loading} onClick={() => { reset(); setRefresh(n => n + 1); }}>Refresh</button></div>
    <form className="history-filters" onSubmit={e => { e.preventDefault(); filter('q', search.trim()); }}>
      <label>Search feedback<input type="search" value={search} maxLength={200} placeholder="Notes, suggested wording or ID" onChange={e => setSearch(e.target.value)} /></label>
      <button type="submit">Search</button>
      <label>Rating<select value={filters.rating} onChange={e => filter('rating', e.target.value)}><option value="down">Needs improvement</option><option value="up">Useful</option><option value="">All ratings</option></select></label>
      <label>Reason<select value={filters.reason} onChange={e => filter('reason', e.target.value)}><option value="">All reasons</option>{Object.entries(feedbackReasons).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label>Source<select value={filters.source} onChange={e => filter('source', e.target.value)}><option value="openai">Live AI reviews</option><option value="demo">Legacy fixtures</option><option value="all">All sources</option></select></label>
      <button type="button" onClick={() => { setSearch(''); reset(); setFilters({ q: '', rating: '', reason: '', source: 'openai' }); }}>Clear filters</button>
    </form>
    <p className="meta">Feedback is not a clinical verdict and does not change results or train the model.</p>
    {error && <p className="error" role="alert">{error} <button onClick={() => setRefresh(n => n + 1)}>Retry feedback</button></p>}
    <ol className="inbox-list" aria-label="Saved feedback entries" aria-busy={loading}>
      {rows.map(({ feedback: entry, report_preview, source, target_comment }) => <li key={entry.id}>
        <div className="saved-feedback-heading"><h2>{entry.rating === 'down' ? <ThumbsDown size={15} /> : <ThumbsUp size={15} />}{entry.reason ? reasonLabel(entry.reason) : entry.rating === 'up' ? 'Useful' : 'Needs improvement'}</h2>
          <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleString()}</time></div>
        <p className="meta">{entry.rating === 'down' ? 'Needs improvement' : 'Useful'} · Result v{entry.result_version} · {entry.target === 'observation' ? `Comment ${entry.observation_id?.replace('obs-', '')}` : entry.target === 'result' ? 'Whole review' : 'Historical flag feedback'} · {source === 'demo' ? 'Legacy fixture' : 'Live AI'}</p>
        {entry.explanation && <p className="feedback-note">{entry.explanation}</p>}
        {entry.suggested_comment && <div className="suggested-wording"><span className="meta">Suggested wording · Feedback only</span><p>{entry.suggested_comment}</p></div>}
        {entry.target === 'observation' && <details className="disclosure disclosure-aside"><summary>Original QA comment</summary><p>{target_comment ?? 'Original comment unavailable for this result version.'}</p></details>}
        <div className="inbox-report"><div><p>{report_preview}</p><span className="meta review-id">{entry.review_id}</span></div><button onClick={() => openReview(entry.review_id)}>Open report</button></div>
      </li>)}
    </ol>
    {loading && <p className="meta" role="status">Loading feedback…</p>}
    {!loading && !error && !rows.length && <div className="empty"><h2>No feedback matches these filters</h2><p>Try all ratings or another source. Save feedback from a completed report to see it here.</p></div>}
    {!!rows.length && <p className="meta">{rows.length} feedback entries shown{cursor ? ' · More available' : ''}</p>}
    {cursor && <button disabled={loading} onClick={() => setAfter(cursor)}>Load more feedback</button>}
  </main>;
}
