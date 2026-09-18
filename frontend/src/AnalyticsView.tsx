import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import { reasonLabel } from './feedbackLabels';
import type { Analytics } from './types';
import { stakeholderLabel } from './OutcomeLog';

export function AnalyticsView() {
  const [period, setPeriod] = useState('7d');
  const [source, setSource] = useState('openai');
  const [subject, setSubject] = useState('report');
  const [refresh, setRefresh] = useState(0);
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    let stopped = false;
    setData(null); setLoading(true); setError('');
    api.analytics(new URLSearchParams({ period, source }).toString()).then(result => {
      if (!stopped) setData(result);
    }).catch(e => { if (!stopped) setError(describeError(e)); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [period, source, refresh]);
  return <main className="history-pane operational-analytics">
    <div className="section-heading"><div><h1>Analytics</h1><p className="meta">Report quality, critical-finding safety, and stakeholder decisions</p></div><button disabled={loading} onClick={() => setRefresh(n => n + 1)}>Refresh</button></div>
    <div className="history-filters">
      <label>Period<select value={period} onChange={e => setPeriod(e.target.value)}><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="all">All time</option></select></label>
      <label>Source<select value={source} onChange={e => setSource(e.target.value)}><option value="openai">Live AI reviews</option><option value="demo">Legacy fixtures</option><option value="all">All sources</option></select></label>
    </div>
    {loading && <p className="meta" role="status">Loading analytics…</p>}
    {error && <p className="error" role="alert">{error} <button onClick={() => setRefresh(n => n + 1)}>Retry analytics</button></p>}
    {data && <>
      <p className="meta">Updated {new Date(data.checked_at).toLocaleString()} · {data.tenant_id}</p>
      <section aria-label="Report quality and acceptance"><h2>Are stakeholders accepting the work?</h2>
        <p className="meta">All matching saved records—not limited to loaded history. A completed QA run is not proof of a correct or accepted report.</p>
        <div className="history-filters"><label>Assess acceptance of<select value={subject} onChange={e => setSubject(e.target.value)}><option value="report">Report</option><option value="qa_comments">QA comments</option></select></label></div>
        {data.acceptance ? <div className="history-table acceptance-table"><table><caption>Operator-recorded decisions · Latest per report and perspective</caption><thead><tr><th>Perspective</th><th>Accepted</th><th>Rejected</th><th>Review requested</th><th>Unknown</th><th>Not recorded</th><th>Acceptance</th></tr></thead><tbody>
          {data.acceptance.filter(row => row.subject === subject).map(row => <tr key={row.stakeholder}><th scope="row">{stakeholderLabel(row.stakeholder)}</th><td>{row.accepted}</td><td>{row.rejected}</td><td>{row.review_requested}</td><td>{row.unknown}</td><td>{row.not_recorded}</td><td>{row.acceptance_rate === null ? 'Not measured' : `${(row.acceptance_rate * 100).toFixed(1)}%`}<small className="meta">{row.accepted} / {row.accepted + row.rejected} final decisions</small></td></tr>)}
        </tbody></table></div> : <p className="meta">Stakeholder outcomes require feedback-read permission.</p>}
        <p className="meta">Denominator: accepted + rejected only. Review requested, unknown and not-recorded outcomes are excluded and shown separately. Record outcomes beneath a completed report's QA comments.</p>
      </section>
      <section aria-label="Critical finding performance"><h2>Are critical findings being missed or overcalled?</h2>
        <p className="meta">Report-level detection in the supplied text—not image diagnosis.</p>
        <div className="measurement-grid">
          {[['Critical recall', 'TP / (TP + FN)', 'How many reference-positive reports did QA surface?'], ['Critical precision', 'TP / (TP + FP)', 'How many flagged reports were reference-positive?'], ['False-positive rate', 'FP / (FP + TN)', 'How often were reference-negative reports flagged?'], ['False-alert share', 'FP / (TP + FP)', 'What share of flagged reports were false alerts?']].map(([label, formula, question]) => <div key={label}><h3>{label}</h3><strong>Not measured</strong><p>{question}</p><span className="meta">{formula}</span></div>)}
        </div>
        <details className="measurement-help"><summary>What is needed to measure this?</summary><p>{data.critical_evaluation.reason}</p><ul><li>Independently adjudicate a representative set of flagged and unflagged reports against a defined critical-finding standard.</li><li>Retain TP, FP, FN, TN counts, indeterminate/excluded cases, coverage, model and skill version, and uncertainty intervals.</li><li>Findings absent from the report cannot count as report-text detection misses. Track those separately as upstream report-quality issues.</li><li>Stakeholder rejection, thumbs down, and reported misses are signals for investigation—not verified false positives or negatives.</li></ul></details>
      </section>
      <section aria-label="Review totals"><h2>Reviews submitted</h2>
        <div className="metric-grid">
          {[[data.reviews.total, 'Submitted'], [data.reviews.statuses.completed, 'Completed'], [data.reviews.critical, 'With critical comments']].map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}
        </div>
        <dl className="metric-details">
          {Object.entries({ 'Queued': data.reviews.statuses.queued, 'Running': data.reviews.statuses.running, 'Input needed': data.reviews.statuses.needs_input, 'Failed': data.reviews.statuses.failed, 'Completed with comments': data.reviews.with_comments, 'Completed without comments': data.reviews.no_comments }).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
        </dl>
        <p className="meta">Current status of reports submitted in this period. Critical-comment reports are a subset of completed reports with comments.</p>
      </section>
      <section aria-label="Feedback totals"><h2>Feedback received</h2>
        {data.feedback ? <>
          <div className="metric-grid">{[[data.feedback.total, 'Entries'], [data.feedback.up, 'Useful'], [data.feedback.down, 'Needs improvement']].map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
          <p className="meta">{data.feedback.reviews} distinct reports · Feedback received in this period, including feedback on older reports. Multiple entries can refer to one report.</p>
          {!!Object.keys(data.feedback.reasons).length && <dl className="metric-details">{Object.entries(data.feedback.reasons).map(([reason, count]) => <div key={reason}><dt>{reasonLabel(reason)}</dt><dd>{count}</dd></div>)}</dl>}
        </> : <p className="meta">Feedback totals require feedback-read permission.</p>}
      </section>
      <p className="analytics-boundary">Operational counts and operator-recorded outcomes—not clinical accuracy, verified stakeholder signatures, or delivery confirmation.</p>
    </>}
  </main>;
}
