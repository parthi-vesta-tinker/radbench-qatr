import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import { reasonLabel } from './feedbackLabels';
import type { Analytics } from './types';
import { stakeholderLabel } from './OutcomeLog';

// Metric definitions stay verbatim from ANALYTICS_SPEC; only their placement changed.
const MEASURES: [string, string, string][] = [
  ['Critical recall', 'TP / (TP + FN)', 'How many reference-positive reports did QA surface?'],
  ['Critical precision', 'TP / (TP + FP)', 'How many flagged reports were reference-positive?'],
  ['False-positive rate', 'FP / (FP + TN)', 'How often were reference-negative reports flagged?'],
  ['False-alert share', 'FP / (TP + FP)', 'What share of flagged reports were false alerts?'],
];

function SectionHeading({ title, status, tier }: { title: string; status: string; tier?: string }) {
  return <div className="section-heading-row">
    <h2>{title}</h2>
    <span className={'section-status ' + (tier ?? '')}>{status}</span>
  </div>;
}

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

  const rows = data?.acceptance?.filter(row => row.subject === subject) ?? [];
  const recorded = rows.reduce((total, row) => total + row.recorded, 0);
  const failed = data?.reviews.statuses.failed ?? 0;

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

      <section aria-label="Report quality and acceptance">
        <SectionHeading title="Are stakeholders accepting the work?" status={data.acceptance ? `${recorded} outcomes · ${rows.length} perspectives` : 'Permission required'}/>
        <p className="meta">All matching saved records—not limited to loaded history. A completed QA run is not proof of a correct or accepted report.</p>
        {data.acceptance ? <>
          <div className="table-caption">
            <p className="meta" id="acceptance-caption">Operator-recorded decisions · Latest per report and perspective</p>
            <div className="section-filter" role="group" aria-label="Assess acceptance of">
              {[['report', 'Report'], ['qa_comments', 'QA comments']].map(([value, label]) =>
                <button key={value} type="button" aria-pressed={subject === value} onClick={() => setSubject(value)}>{label}</button>)}
            </div>
          </div>
          <div className="history-table acceptance-table" role="region" aria-labelledby="acceptance-caption" tabIndex={0}>
            <table aria-describedby="acceptance-caption"><thead><tr><th>Perspective</th><th>Accepted</th><th>Rejected</th><th>Review requested</th><th>Unknown</th><th>Not recorded</th><th>Acceptance</th></tr></thead><tbody>
              {rows.map(row => <tr key={row.stakeholder}>
                <th scope="row">{stakeholderLabel(row.stakeholder)}</th>
                <td data-label="Accepted">{row.accepted}</td>
                <td data-label="Rejected">{row.rejected}</td>
                <td data-label="Review requested">{row.review_requested}</td>
                <td data-label="Unknown">{row.unknown}</td>
                <td data-label="Not recorded">{row.not_recorded}</td>
                <td data-label="Acceptance">{row.acceptance_rate === null ? 'Not measured' : `${(row.acceptance_rate * 100).toFixed(1)}%`}<small className="meta">{row.accepted} / {row.accepted + row.rejected} final decisions</small></td>
              </tr>)}
            </tbody></table>
          </div>
        </> : <p className="meta">Stakeholder outcomes require feedback-read permission.</p>}
        <p className="meta">Denominator: accepted + rejected only. Review requested, unknown and not-recorded outcomes are excluded and shown separately. Record outcomes beneath a completed report's QA comments.</p>
      </section>

      <section aria-label="Review totals">
        <SectionHeading title="Are reviews completing?" status={`${data.reviews.total} submitted${failed ? ` · ${failed} failed` : ''}`} tier={failed ? 'danger' : ''}/>
        <div className="metric-grid">
          {[[data.reviews.total, 'Submitted'], [data.reviews.statuses.completed, 'Completed'], [data.reviews.critical, 'With critical comments']].map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}
        </div>
        <dl className="metric-details">
          {Object.entries({ 'Queued': data.reviews.statuses.queued, 'Running': data.reviews.statuses.running, 'Input needed': data.reviews.statuses.needs_input, 'Failed': data.reviews.statuses.failed, 'Completed with comments': data.reviews.with_comments, 'Completed without comments': data.reviews.no_comments }).map(([label, value]) => <div key={label} className={label === 'Failed' && value ? 'danger' : ''}><dt>{label}</dt><dd>{value}</dd></div>)}
        </dl>
        <p className="meta">Current status of reports submitted in this period. Critical-comment reports are a subset of completed reports with comments.</p>
      </section>

      <section aria-label="Feedback totals">
        <SectionHeading title="What do users want improved?" status={data.feedback ? `${data.feedback.total} entries · ${data.feedback.reviews} reports` : 'Permission required'}/>
        {data.feedback ? <>
          <div className="metric-grid">{[[data.feedback.total, 'Entries'], [data.feedback.up, 'Useful'], [data.feedback.down, 'Needs improvement']].map(([value, label]) => <div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
          <p className="meta">{data.feedback.reviews} distinct reports · Feedback received in this period, including feedback on older reports. Multiple entries can refer to one report.</p>
          {!!Object.keys(data.feedback.reasons).length && <dl className="metric-details">{Object.entries(data.feedback.reasons).map(([reason, count]) => <div key={reason}><dt>{reasonLabel(reason)}</dt><dd>{count}</dd></div>)}</dl>}
        </> : <p className="meta">Feedback totals require feedback-read permission.</p>}
      </section>

      <section aria-label="Critical finding performance">
        <SectionHeading title="Are critical findings being missed or overcalled?" status="Not measured" tier="attention"/>
        <p className="critical-reason">{data.critical_evaluation.reason}</p>
        <p className="meta">Report-level detection in the supplied text—not image diagnosis.</p>
        <details className="disclosure disclosure-aside measurement-help">
          <summary>What is needed to measure this?</summary>
          <dl className="measurement-list">
            {MEASURES.map(([label, formula, question]) => <div key={label}>
              <dt>{label} <code>{formula}</code></dt>
              <dd>{question} <strong>Not measured.</strong></dd>
            </div>)}
          </dl>
          <ul>
            <li>Independently adjudicate a representative set of flagged and unflagged reports against a defined critical-finding standard.</li>
            <li>Retain TP, FP, FN, TN counts, indeterminate/excluded cases, coverage, model and skill version, and uncertainty intervals.</li>
            <li>Findings absent from the report cannot count as report-text detection misses. Track those separately as upstream report-quality issues.</li>
            <li>Stakeholder rejection, thumbs down, and reported misses are signals for investigation—not verified false positives or negatives.</li>
          </ul>
        </details>
      </section>

      <p className="analytics-boundary">Operational counts and operator-recorded outcomes—not clinical accuracy, verified stakeholder signatures, or delivery confirmation.</p>
    </>}
  </main>;
}
