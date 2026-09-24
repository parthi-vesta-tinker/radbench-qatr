import { RefreshCw } from 'lucide-react';
import { TooltipButton } from './TooltipButton';
import { useEffect, useState } from 'react';
import { api, describeError } from './api';
import type { Analytics } from './types';

const PERIODS: { value: Analytics['period']; label: string }[] = [
  { value: '1h', label: 'Last hour' },
  { value: '6h', label: 'Last 6 hours' },
  { value: '12h', label: 'Last 12 hours' },
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: 'all', label: 'All time' },
];

export function AnalyticsView() {
  const [period, setPeriod] = useState<Analytics['period']>('24h');
  const [refresh, setRefresh] = useState(0);
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let stopped = false;
    setData(null); setLoading(true); setError('');
    api.analytics(new URLSearchParams({ period, source: 'all' }).toString()).then(result => {
      if (!stopped) setData(result);
    }).catch(e => { if (!stopped) setError(describeError(e)); })
      .finally(() => { if (!stopped) setLoading(false); });
    return () => { stopped = true; };
  }, [period, refresh]);

  const pending = data ? data.reviews.statuses.queued + data.reviews.statuses.running : 0;
  const inputNeeded = data?.reviews.statuses.needs_input ?? 0;

  return <main className="history-pane operational-analytics">
    <div className="section-heading analytics-heading">
      <h1>Analytics</h1>
      <div className="analytics-controls">
        <label htmlFor="analytics-period">Period</label>
        <select id="analytics-period" value={period} onChange={e => setPeriod(e.target.value as Analytics['period'])}>
          {PERIODS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        <TooltipButton className="icon-button" side="left" label="Refresh analytics" disabled={loading} onClick={() => setRefresh(n => n + 1)}><RefreshCw size={19} aria-hidden="true" /></TooltipButton>
      </div>
    </div>
    {loading && <p className="meta" role="status">Loading analytics…</p>}
    {error && <p className="error" role="alert">{error} <button onClick={() => setRefresh(n => n + 1)}>Retry analytics</button></p>}
    {data && <>
      <section className="analytics-findings" aria-label="Review findings">
        <h2>Review findings</h2>
        <dl className="analytics-metrics analytics-metrics-primary">
          <div><dt>Inconsistencies</dt><dd>{data.findings.inconsistencies}</dd></div>
          <div><dt>Critical findings</dt><dd>{data.findings.critical_findings}</dd></div>
          <div><dt>Clinical observations</dt><dd>{data.findings.clinical_observations}</dd></div>
          <div><dt>Other issues</dt><dd>{data.findings.other_issues}</dd></div>
        </dl>
      </section>
      <section className="analytics-classification" aria-label="Classification counts">
        <h2>Classification</h2>
        {Object.keys(data.classification?.finding_groups ?? {}).length ? <div className="analytics-classification-groups">
          <div><h3>Finding group</h3><dl>{Object.entries(data.classification?.finding_groups ?? {}).sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0])).map(([label, count]) =>
            <div key={label}><dt>{label.replaceAll('_',' ').replace(/^./, value => value.toUpperCase())}</dt><dd>{count}</dd></div>
          )}</dl></div>
          <div><h3>Communication priority</h3><dl>{['minutes','hours','days','routine','cannot_determine'].filter(label => (data.classification?.communication_priorities?.[label] ?? 0) > 0).map(label =>
            <div key={label}><dt>{label.replaceAll('_',' ').replace(/^./, value => value.toUpperCase())}</dt><dd>{data.classification?.communication_priorities?.[label]}</dd></div>
          )}</dl></div>
        </div> : <p className="meta">No classifications available.</p>}
      </section>
      <section className="analytics-activity" aria-label="Review activity">
        <h2>Review activity</h2>
        <dl className="analytics-metrics analytics-metrics-secondary">
          <div><dt>Submitted</dt><dd>{data.reviews.total}</dd></div>
          <div><dt>Completed</dt><dd>{data.reviews.statuses.completed}</dd></div>
          <div><dt>Failed</dt><dd>{data.reviews.statuses.failed}</dd></div>
        </dl>
        {(pending > 0 || inputNeeded > 0) && <p className="meta analytics-pending">
          {pending > 0 && `${pending} queued or running`}
          {pending > 0 && inputNeeded > 0 && ' · '}
          {inputNeeded > 0 && `${inputNeeded} need input`}
        </p>}
      </section>
    </>}
  </main>;
}
