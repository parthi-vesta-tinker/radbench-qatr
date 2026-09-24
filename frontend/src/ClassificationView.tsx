import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, LoaderCircle } from 'lucide-react';
import { api, ApiError, describeError } from './api';
import type { ClassificationAnalysis, ClassificationResource, Review } from './types';
import type { ClassificationData } from './useClassification';
import { fields, format, names, ResultCard } from './FindingClassification';

function Analysis({run, refresh, ready, stale}: {run: ClassificationResource; refresh: () => void; ready: boolean; stale: boolean}) {
  const [analysis, setAnalysis] = useState<ClassificationAnalysis | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const requestKey = useRef<string | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => {
    let cancelled = false;
    setAnalysis(null); setError('');
    api.classificationAnalysis(run.id).then(value => { if (!cancelled) setAnalysis(value); })
      .catch(cause => { if (!cancelled) setError(describeError(cause)); });
    return () => { cancelled = true; };
  }, [run.id, revision]);
  async function retry() {
    if (busy || stale || !ready) return;
    setBusy(true); setError('');
    try {
      requestKey.current ||= crypto.randomUUID();
      await api.classify({review_id: run.review_id, input_version: run.input_version, observation_id: run.observation_id}, requestKey.current);
      requestKey.current = null;
      if (mounted.current) refresh();
    } catch (cause) {
      if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) requestKey.current = null;
      if (mounted.current) setError(describeError(cause));
    } finally { if (mounted.current) setBusy(false); }
  }
  return <div className="classification-analysis">
    {error && <p role="alert" className="notice">{error} <button onClick={() => setRevision(n => n + 1)}>Retry details</button></p>}
    {analysis && <>
      <details className="jev-details"><summary>State · Inputs sent to JEV</summary>
        <dl className="classification-state"><div><dt>Finding text</dt><dd>{analysis.state.finding_text}</dd></div>
          <div><dt>QA comment</dt><dd>{analysis.state.qa_comment}</dd></div>
          <div><dt>Report quotes</dt><dd>{analysis.state.report_quotes.length ? analysis.state.report_quotes.map((quote, i) => <blockquote key={i}>{quote}</blockquote>) : 'None'}</dd></div></dl>
      </details>
      <h3>Classification breakdown</h3>
      {fields.map(field => {
        const answer = run.result?.fields[field];
        const question = analysis.questions[field];
        return <section className="classification-field" key={field}>
          <div className="section-heading"><h4>{names[field]}</h4>{answer && <strong>{format(answer.label)}</strong>}</div>
          {answer && <>
            <div className="classification-probabilities" aria-label={`${names[field]} probabilities`}>
              {Object.entries(answer.raw_probabilities).sort((a, b) => b[1] - a[1]).map(([label, probability]) => <div key={label}>
                <span>{format(label)}</span><meter min={0} max={1} value={probability} aria-label={format(label)}/><span>{(probability * 100).toFixed(1)}%</span>
              </div>)}
            </div>
            <p className="meta">Raw model probability · Top {(answer.top_probability * 100).toFixed(1)}% · Margin {(answer.margin * 100).toFixed(1)}% · Provider confidence {(answer.provider_confidence * 100).toFixed(1)}%</p>
            {answer.calibrated_probabilities && <details><summary>Calibrated probabilities</summary><dl className="classification-criteria">{Object.entries(answer.calibrated_probabilities).map(([label, value]) => <div key={label}><dt>{format(label)}</dt><dd>{(value * 100).toFixed(1)}%</dd></div>)}</dl></details>}
            {answer.review_reasons?.map(reason => <p className="meta" key={reason}>{reason}</p>)}
          </>}
          {question && <details className="jev-details"><summary>Question and criteria</summary>
            <p className="classification-instructions">{question.instructions}</p>
            <dl className="classification-criteria">{Object.entries(question.criteria).map(([label, criterion]) => <div key={label}><dt>{format(label)}</dt><dd>{criterion}</dd></div>)}</dl>
          </details>}
        </section>;
      })}
    </>}
    <details className="jev-details"><summary>Run details</summary>
      <dl className="classification-criteria">
        <div><dt>Classification ID</dt><dd>{run.id}</dd></div>
        <div><dt>Status</dt><dd>{format(run.execution_status)}</dd></div>
        <div><dt>Model</dt><dd>{run.provenance.model}</dd></div>
        <div><dt>Rubric</dt><dd>{analysis ? `${analysis.rubric_id} · ${analysis.rubric_version} · ${format(analysis.rubric_status)}` : run.provenance.rubric_id}</dd></div>
        <div><dt>Input hash</dt><dd>{run.input_hash}</dd></div>
        <div><dt>Rubric hash</dt><dd>{analysis?.rubric_hash ?? run.provenance.rubric_hash}</dd></div>
        <div><dt>Calibration</dt><dd>{run.result ? format(run.result.calibration_status) : '—'}{run.result?.calibrator_id ? ` · ${run.result.calibrator_id}` : ''}</dd></div>
        <div><dt>Started</dt><dd>{new Date(run.created_at).toLocaleString()}</dd></div>
        <div><dt>Updated</dt><dd>{new Date(run.updated_at).toLocaleString()}</dd></div>
        {run.result?.duration_ms != null && <div><dt>Provider duration</dt><dd>{run.result.duration_ms} ms</dd></div>}
        {run.result?.usage && <div><dt>Tokens</dt><dd>{run.result.usage.input_tokens} input · {run.result.usage.output_tokens} output</dd></div>}
        {run.steps.map((step, i) => <div key={i}><dt>{format(String(step.step_id))}</dt><dd>{format(String(step.status))}</dd></div>)}
      </dl>
      {run.error && <p role="alert" className="notice">{run.error.message} <span className="meta">{run.error.code}</span></p>}
      {run.execution_status === 'failed' && ready && <button disabled={busy || stale} onClick={() => void retry()}>{busy ? 'Starting…' : 'Try as new request'}</button>}
    </details>
  </div>;
}

function StartClassification({review, observationId, refresh}: {review: Review; observationId: string; refresh: () => void}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const key = useRef<string | null>(null);
  async function start() {
    if (busy) return;
    setBusy(true); setError('');
    key.current ||= crypto.randomUUID();
    try {
      await api.classify({review_id:review.id, input_version:review.input_version, observation_id:observationId}, key.current);
      key.current = null;
      refresh();
    } catch (cause) {
      if (cause instanceof ApiError && cause.status >= 400 && cause.status < 500) key.current = null;
      setError(describeError(cause));
    } finally { setBusy(false); }
  }
  return <div className="jev-actions"><button disabled={busy} onClick={() => void start()}>{busy ? 'Starting…' : 'Classify finding'}</button>{error && <p role="alert">{error}</p>}</div>;
}

export function ClassificationView({review, stale, data, backToReport}: {review: Review | null; stale: boolean; data: ClassificationData; backToReport: () => void}) {
  const [selected, setSelected] = useState('');
  const current = !stale && review?.execution_status === 'completed';
  const noCriticalFindings = current && review?.result?.critical_comments.length === 0;
  const run = current ? data.runs.find(item => item.observation_id === selected) ?? data.runs[0] : undefined;
  return <main className="history-pane classification-pane">
    <button type="button" className="linklike classification-back" onClick={backToReport}><ArrowLeft size={16}/>Back to report</button>
    <div className="section-heading"><h1>Classification</h1>{current && <span className="meta">Review {review.id.slice(-5).toUpperCase()}</span>}</div>
    {!review || stale ? <p className="meta">Review this report to see classification.</p> : !run && !data.loading ? <p className="meta">{noCriticalFindings ? "No critical findings were reported. Classification is not applicable." : "No classification available."}</p> : null}
    {data.loading && <span className="jev-loading" role="status" aria-label="Loading classification"><LoaderCircle className="journey-spinner" size={18}/></span>}
    {data.error && <p className="notice" role="alert">{data.error} <button onClick={data.refresh}>Retry</button></p>}
    {current && data.runs.length > 1 && <label className="classification-select">Finding<select value={run?.observation_id ?? ''} onChange={event => setSelected(event.target.value)}>
      {data.runs.map((item, index) => <option key={item.id} value={item.observation_id}>Finding {index + 1} · {item.input.finding_text.slice(0, 80)}</option>)}
    </select></label>}
    {current && !data.loading && data.config?.ready && review.result?.critical_comments.filter(observation => !data.runs.some(item => item.observation_id === observation.observation_id)).map(observation =>
      <StartClassification key={`${review.id}:${review.input_version}:${observation.observation_id}`} review={review} observationId={observation.observation_id} refresh={data.refresh}/>
    )}
    {run && <>
      <ResultCard key={run.id} run={run} config={data.config} stale={stale}/>
      <Analysis key={`analysis:${run.id}`} run={run} refresh={data.refresh} ready={Boolean(data.config?.ready)} stale={stale}/>
    </>}
  </main>;
}
