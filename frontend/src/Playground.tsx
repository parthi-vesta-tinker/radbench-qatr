import { useEffect, useRef, useState } from 'react';
import { Check, Search } from 'lucide-react';
import { api, describeError } from './api';
import type { PlaygroundCatalog, PlaygroundRun, PlaygroundSample } from './types';

const PHASES: Record<string, string> = {
  input_validation: 'Input validation',
  combined_review: 'Combined report review',
  output_validation: 'Output validation',
  comment_assembly: 'Comment assembly',
};

const SAMPLE_TITLES: Record<string, string> = {
  'critical-documented': 'Documented critical flag',
  'critical-flagged': 'Flagged critical finding',
  'critical-uncertain': 'Uncertain critical concern',
  'laterality-swap': 'Laterality mismatch',
  'impression-contradiction': 'Recommendation mismatch',
  'technique-conflict': 'Technique conflict',
};
const sampleTitle = (sample: PlaygroundSample) => SAMPLE_TITLES[sample.sample_id] ?? sample.title;
const categoryTitle = (id: string, title: string) => id === 'inconsistency' ? 'Findings & impression' : title;

function elapsed(ms: number | null | undefined) {
  if (ms === null || ms === undefined) return '';
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function Playground({ active, openSkills, settingsRevision = 0, skillsEnabled = true }: { active: boolean; openSkills: () => void; settingsRevision?: number; skillsEnabled?: boolean }) {
  const [catalog, setCatalog] = useState<PlaygroundCatalog | null>(null);
  const [catalogError, setCatalogError] = useState('');
  const [selected, setSelected] = useState('');
  const [source, setSource] = useState<'sample' | 'paste'>('sample');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [pasted, setPasted] = useState('');
  const [model, setModel] = useState('');
  const [run, setRun] = useState<PlaygroundRun | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const polling = useRef<number | undefined>(undefined);

  useEffect(() => {
    let stopped = false;
    api.playground()
      .then(data => { if (!stopped) { setCatalog(data); setModel(old => old || data.models[0] || ''); setSelected(old => old || data.samples[0]?.sample_id || ''); } })
      .catch(e => { if (!stopped) setCatalogError(describeError(e)); });
    return () => { stopped = true; };
  }, [settingsRevision]);

  // A run is followed only while this screen owns it. There is no run history to return to.
  useEffect(() => {
    if (!run || ['completed', 'failed', 'needs_input'].includes(run.status)) return;
    polling.current = window.setTimeout(() => {
      api.playgroundRun(run.run_id).then(setRun).catch(e => setError(describeError(e)));
    }, 900);
    return () => window.clearTimeout(polling.current);
  }, [run]);

  const demoMode = catalog?.run_mode === 'demo';
  const samples = catalog?.samples ?? [];
  const chosen = source === 'sample' ? samples.find(s => s.sample_id === selected) : undefined;
  const usingPaste = source === 'paste' && pasted.trim().length > 0;
  const running = Boolean(run && ['queued', 'running'].includes(run.status));
  const locked = busy || running;
  const query = search.trim().toLocaleLowerCase();
  const visibleSamples = samples.filter(sample => (!category || sample.category === category)
    && (!query || `${sampleTitle(sample)} ${sample.title} ${sample.report_text}`.toLocaleLowerCase().includes(query)));
  const chosenCategory = catalog?.categories.find(item => item.id === chosen?.category);
  const blocked = Boolean(chosen && demoMode && !chosen.demo_supported);
  const canRun = Boolean(catalog?.ready) && !locked && (Boolean(chosen) || usingPaste) && !blocked;

  function pick(sample: PlaygroundSample) {
    if (locked || selected === sample.sample_id) return;
    setSelected(sample.sample_id);
    setRun(null);
    setError('');
  }

  function changeSource(next: 'sample' | 'paste') {
    if (locked || source === next) return;
    setSource(next); setRun(null); setError('');
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
      <h1>Playground</h1>
      {skillsEnabled && <button type="button" className="linklike" onClick={openSkills}>Skills</button>}
    </div>
    {catalogError && <p className="error" role="alert">{catalogError}</p>}
    {!catalog && !catalogError && <p role="status">Loading playground…</p>}
    {catalog && <>
      <div className="playground-source" role="group" aria-label="Report source">
        <button type="button" aria-pressed={source === 'sample'} disabled={locked} onClick={() => changeSource('sample')}>Sample reports</button>
        <button type="button" aria-pressed={source === 'paste'} disabled={locked} onClick={() => changeSource('paste')}>Paste report</button>
      </div>

      <div className={'playground-workbench' + (source === 'paste' ? ' paste-mode' : '')}>
        {source === 'sample' && <section className="playground-library" aria-label="Sample reports">
          <div className="playground-filters">
            <label className="playground-search"><Search size={16} aria-hidden="true"/>
              <input type="search" aria-label="Search samples" placeholder="Search samples" value={search} onChange={e => setSearch(e.target.value)}/>
            </label>
            <select aria-label="Use case" value={category} onChange={e => setCategory(e.target.value)}>
              <option value="">All use cases</option>
              {catalog.categories.map(item => <option key={item.id} value={item.id}>{categoryTitle(item.id, item.title)}</option>)}
            </select>
          </div>
          <div className="playground-sample-list">
            {catalog.categories.map(item => {
              const group = visibleSamples.filter(sample => sample.category === item.id);
              return group.length > 0 && <section key={item.id} className="playground-category">
                <h2>{categoryTitle(item.id, item.title)}<span>{group.length}</span></h2>
                {group.map(sample => <button key={sample.sample_id} type="button"
                  className={'playground-sample' + (selected === sample.sample_id ? ' selected' : '')}
                  aria-pressed={selected === sample.sample_id} disabled={locked} onClick={() => pick(sample)}>
                  <span><strong>{sampleTitle(sample)}</strong>
                    {demoMode && <span className="meta">{sample.demo_supported ? 'Runs in demo' : 'Model required'}</span>}
                  </span>
                  {selected === sample.sample_id && <Check size={16} aria-hidden="true"/>}
                </button>)}
              </section>;
            })}
            {!visibleSamples.length && <div className="playground-no-matches" role="status">
              <p>{samples.length ? 'No matching samples.' : 'No samples available.'}</p>
              {samples.length > 0 && <button type="button" className="linklike" onClick={() => { setSearch(''); setCategory(''); }}>Clear filters</button>}
            </div>}
          </div>
        </section>}

        <section className="playground-reader" aria-label={source === 'sample' ? 'Selected report' : 'Paste report'}>
          <div className="playground-report-body">
            {source === 'sample' ? chosen ? <>
              <div className="playground-report-heading">
                <h2>{sampleTitle(chosen)}</h2>
                {chosenCategory && <p className="meta">{categoryTitle(chosenCategory.id, chosenCategory.title)}</p>}
              </div>
              <pre className="playground-report-text" tabIndex={0} aria-label="Sample report text">{chosen.report_text}</pre>
            </> : <p className="meta">Select a sample to preview its report.</p> : <div className="playground-paste">
              <label htmlFor="playground-report">Report text</label>
              <textarea id="playground-report" value={pasted} rows={12} spellCheck={false} maxLength={40000}
                disabled={locked} placeholder={'Findings:\nPaste findings here.\n\nImpression:\nPaste impression here.'}
                onChange={e => { setPasted(e.target.value); setRun(null); setError(''); }}/>
            </div>}
          </div>
          <div className="playground-run-controls">
            {blocked && <p className="notice">This sample needs a configured model. Choose a sample marked “Runs in demo”.</p>}
            {!catalog.ready && <p className="notice">Configure a model and API key to run.</p>}
            <div className="playground-actions">
              <label htmlFor="playground-model">Model
                <select id="playground-model" value={model} disabled={locked} onChange={e => { setModel(e.target.value); setRun(null); }}>
                  {catalog.models.map(m => <option key={m} value={m}>{m}</option>)}
                </select>
              </label>
              <button className="primary" disabled={!canRun} onClick={() => void startRun()}>
                {busy ? 'Starting…' : running ? 'Running…' : 'Run test review'}
              </button>
            </div>
            {catalog.run_mode === 'live' && catalog.live_model && catalog.live_model !== model &&
              <p className="meta">Live model: {catalog.live_model}</p>}
            {demoMode && <p className="meta">Demo mode</p>}
            {error && <p className="error" role="alert">{error}</p>}
          </div>
        </section>
      </div>
      <details className="playground-configuration">
        <summary>Configuration <span className="meta">· Pack {catalog.pack_version} · {catalog.skills.length} skills</span></summary>
        <p className="meta">{catalog.pack_release}</p>
        {skillsEnabled && <button type="button" className="linklike" onClick={openSkills}>View skills</button>}
      </details>

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
            <h4>PACS comments</h4>
            {result.general_comments?.length
              ? <ol className="playground-comments">{result.general_comments.map(c => <li key={c.observation_id}>{c.comment}</li>)}</ol>
              : <p className="meta">None.</p>}
            <h4>Critical findings comments</h4>
            {result.critical_comments?.length
              ? <ol className="playground-comments">{result.critical_comments.map(c => <li key={c.observation_id}>{c.comment}</li>)}</ol>
              : <p className="meta">None.</p>}
          </>}
          {['queued', 'running'].includes(run.status) && <p role="status">Running…</p>}
        </section>
      </div>}
    </>}
  </main>;
}
