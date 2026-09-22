import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import { reasonLabel } from './feedbackLabels';
import type { Analytics } from './types';

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

  const failed = data?.reviews.statuses.failed ?? 0;

  return <main className="history-pane operational-analytics">
    <div className="section-heading"><div><h1>Analytics</h1><p className="meta">Review completion, feedback, and critical-finding measures</p></div><button disabled={loading} onClick={() => setRefresh(n => n + 1)}>Refresh</button></div>
    <div className="history-filters">
      <label>Period<select value={period} onChange={e => setPeriod(e.target.value)}><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="all">All time</option></select></label>
      <label>Source<select value={source} onChange={e => setSource(e.target.value)}><option value="openai">Live AI reviews</option><option value="demo">Legacy fixtures</option><option value="all">All sources</option></select></label>
    </div>
    {loading && <p className="meta" role="status">Loading analytics…</p>}
    {error && <p className="error" role="alert">{error} <button onClick={() => setRefresh(n => n + 1)}>Retry analytics</button></p>}
    {data && <>
      <p className="meta">Updated {new Date(data.checked_at).toLocaleString()} · {data.tenant_id}</p>

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

      <p className="analytics-boundary">Operational counts do not establish clinical accuracy or delivery confirmation.</p>
    </>}
  </main>;
}
