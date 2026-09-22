import { useEffect, useRef, useState } from 'react';
import { FlaskConical, ExternalLink } from 'lucide-react';
import { api, describeError } from './api';
import type { PlaygroundCatalog, PlaygroundRun, PlaygroundSample } from './types';

const PHASES: Record<string, string> = {
  input_validation: 'Input validation',
  combined_review: 'Combined report review',
  output_validation: 'Output validation',
  comment_assembly: 'Comment assembly',
};

function elapsed(ms: number | null | undefined) {
  if (ms === null || ms === undefined) return '';
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function Playground({ active, openSkills }: { active: boolean; openSkills: () => void }) {
  const [catalog, setCatalog] = useState<PlaygroundCatalog | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [selected, setSelected] = useState('');
  const [pasted, setPasted] = useState('');
  const [model, setModel] = useState('');
  const [run, setRun] = useState<PlaygroundRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const polling = useRef<number | undefined>(undefined);

  useEffect(() => {
    let stopped = false;
    api.playground()
      .then(data => { if (!stopped) { setCatalog(data); setModel(old => old || data.models[0] || ''); } })
      .catch(e => { if (!stopped) setCatalogError(describeError(e)); });
    return () => { stopped = true; };
  }, []);

  // A run is followed only while this screen owns it. There is no run history to return to.
  useEffect(() => {
    if (!run || ['completed', 'failed', 'needs_input'].includes(run.status)) return;
    polling.current = window.setTimeout(() => {
      api.playgroundRun(run.run_id).then(setRun).catch(e => setError(describeError(e)));
    }, 900);
    return () => window.clearTimeout(polling.current);
  }, [run]);

  const demoMode = catalog?.mode === 'demo';
  const samples = catalog?.samples ?? [];
  const chosen = samples.find(s => s.sample_id === selected);
  const usingPaste = !selected && pasted.trim().length > 0;
  const blocked = Boolean(chosen && demoMode && !chosen.demo_supported);
  const canRun = Boolean(catalog?.ready) && !busy && (Boolean(chosen) || usingPaste) && !blocked;

  function pick(sample: PlaygroundSample) {
    setSelected(sample.sample_id === selected ? '' : sample.sample_id);
    setPasted('');
    setRun(null);
    setError('');
  }

  async function startRun() {
    if (!canRun) return;
    setBusy(true); setError(''); setRun(null);
    try {
      const started = await api.startPlaygroundRun(
        { model, ...(chosen ? { sample_id: chosen.sample_id } : { report_text: pasted }) },
        crypto.randomUUID(),
      );
      setRun(started);
    } catch (e) { setError(describeError(e)); }
    finally { setBusy(false); }
  }

  const result = run?.result as {
    general_comments?: { observation_id: string; comment: string }[];
    critical_comments?: { observation_id: string; comment: string }[];
    outcome?: string;
  } | null | undefined;

  return <main className="history-pane playground-pane" hidden={!active}>
    <div className="section-heading">
      <div>
        <h1>Playground</h1>
        <p className="meta">Try report QA on sample reports. Nothing here becomes a review.</p>
      </div>
    </div>
    <p className="playground-banner" role="note">
      <FlaskConical size={16} aria-hidden="true"/>
      <span><strong>Playground — not a clinical review.</strong> {catalog?.boundary ?? 'Output is never stored as a review and has no copy actions.'}</span>
    </p>
    {catalogError && <p className="error" role="alert">{catalogError}</p>}
    {!catalog && !catalogError && <p role="status">Loading playground…</p>}
    {catalog && <>
      <div className="playground-setup">
        <p className="meta">
          Instructions: pack <strong>{catalog.pack_version}</strong> · {catalog.skills.length} skills, used as one set and not editable here.
          {' '}<button type="button" className="linklike" onClick={openSkills}>Read them in Skills <ExternalLink size={13} aria-hidden="true"/></button>
        </p>
        <label htmlFor="playground-model">Model
          <select id="playground-model" value={model} disabled={busy} onChange={e => setModel(e.target.value)}>
            {catalog.models.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </label>
        {catalog.mode === 'openai' && catalog.live_model && catalog.live_model !== model &&
          <p className="meta">Live review currently uses <strong>{catalog.live_model}</strong>. A different model here will not predict live output.</p>}
        {demoMode && <p className="notice">Demo mode: canned output, no provider call. Samples marked <em>demo</em> can run; the others need a configured model.</p>}
        {!catalog.ready && <p className="notice">Live review is not configured. Set the backend model and OpenAI key to run the playground.</p>}
      </div>

      {catalog.categories.map(category => <section key={category.id} className="playground-category">
        <h2>{category.title}</h2>
        <p className="meta">{category.description}</p>
        <div className="playground-samples">
          {samples.filter(s => s.category === category.id).map(sample => <button
            key={sample.sample_id}
            type="button"
            className={'playground-sample' + (selected === sample.sample_id ? ' selected' : '')}
            aria-pressed={selected === sample.sample_id}
            disabled={busy}
            onClick={() => pick(sample)}>
            <strong>{sample.title}</strong>
            <span className="meta">{sample.demo_supported ? 'Runs in demo' : 'Needs a model'}</span>
          </button>)}
        </div>
      </section>)}

      {chosen && <div className="playground-preview">
        <div className="section-heading"><h3>Selected report</h3><span className="meta">Synthetic test fixture</span></div>
        <pre>{chosen.report_text}</pre>
        {blocked && <p className="notice">This sample needs a configured model. In demo mode, choose a sample marked “Runs in demo”.</p>}
      </div>}

      <div className="playground-paste">
        <label htmlFor="playground-report">Or paste your own report</label>
        <textarea id="playground-report" value={pasted} rows={5} spellCheck={false} maxLength={40000}
          disabled={busy || Boolean(selected)}
          placeholder={'Findings:\nPaste findings here.\n\nImpression:\nPaste impression here.'}
          onChange={e => { setPasted(e.target.value); setRun(null); }}/>
        <p className="meta">Use synthetic text. This is a test surface, not a clinical record.</p>
      </div>

      <div className="playground-actions">
        <button className="primary" disabled={!canRun} onClick={() => void startRun()}>
          {busy ? 'Starting…' : 'Run test review'}
        </button>
        {run && <span className="meta">Run {run.run_id.slice(0, 11)} · {run.model} · {run.status.replaceAll('_', ' ')}</span>}
      </div>
      {error && <p className="error" role="alert">{error}</p>}

      {run && <div className="playground-result">
        <section aria-label="Run log">
          <h3>Log</h3>
          <ol className="playground-log">
            {run.steps.map(step => <li key={step.step} data-status={step.status}>
              <span>{PHASES[step.step] ?? step.step}</span>
              <span className="meta">{step.status.replaceAll('_', ' ')}{step.elapsed_ms != null ? ` · ${elapsed(step.elapsed_ms)}` : ''}</span>
            </li>)}
          </ol>
        </section>
        <section aria-label="Review results">
          <h3>Results</h3>
          {run.error && <p className="error" role="alert">{String((run.error as {message?: string}).message ?? 'The run did not finish.')} [{String((run.error as {code?: string}).code ?? '')}]</p>}
          {run.status === 'completed' && result && <>
            <h4>General comments</h4>
            {result.general_comments?.length
              ? <ol className="playground-comments">{result.general_comments.map(c => <li key={c.observation_id}>{c.comment}</li>)}</ol>
              : <p className="meta">None.</p>}
            <h4>Critical findings comments</h4>
            {result.critical_comments?.length
              ? <ol className="playground-comments">{result.critical_comments.map(c => <li key={c.observation_id}>{c.comment}</li>)}</ol>
              : <p className="meta">None.</p>}
            <p className="meta">Copying is unavailable in the playground, so a test comment cannot reach a real report.</p>
          </>}
          {['queued', 'running'].includes(run.status) && <p role="status">Running…</p>}
        </section>
      </div>}
    </>}
  </main>;
}
