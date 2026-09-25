import {useEffect, useRef, useState} from 'react';
import {X} from 'lucide-react';
import {api, describeError} from './api';
import type {AppSettings, Features, SettingsUpdate} from './types';

const accessLabels = {local:'Local', public:'Public', api_key:'API key required'};
const featureLabels: {key:keyof Features; title:string; description:string}[] = [
  {key:'playground', title:'Playground', description:'Test reports'},
  {key:'skills', title:'Skills', description:'Edit instructions'},
  {key:'classification', title:'CF classification', description:'Critical findings'},
  {key:'classification_analysis', title:'Classification analysis', description:'Full screen'},
];

export function SettingsPanel({close, saved}: {close:()=>void; saved:(value:AppSettings)=>void}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const opener = useRef(document.activeElement as HTMLElement | null);
  const [settings,setSettings] = useState<AppSettings|null>(null);
  const [draft,setDraft] = useState<SettingsUpdate|null>(null);
  const [busy,setBusy] = useState(false);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState('');
  const [attempt,setAttempt] = useState(0);
  useEffect(()=>{const element=dialog.current;element?.showModal();return()=>{element?.close();queueMicrotask(()=>opener.current?.focus());};},[]);
  useEffect(()=>{
    let stopped=false;
    setLoading(true);setError('');
    api.settings().then(value=>{
      if(stopped)return;
      setSettings(value);
      const {revision,run_mode,core_model,features}=value;
      setDraft({revision,run_mode,core_model,features});
    }).catch(e=>{if(!stopped)setError(describeError(e));})
      .finally(()=>{if(!stopped)setLoading(false);});
    return()=>{stopped=true;};
  },[attempt]);
  function change(value:Partial<SettingsUpdate>){setDraft(old=>old?{...old,...value}:old);}
  const changed = !!(settings && draft && (draft.run_mode !== settings.run_mode ||
    draft.core_model !== settings.core_model || featureLabels.some(({key}) => draft.features[key] !== settings.features[key])));
  async function save(){
    if(!draft || busy || !settings?.can_edit || !changed)return;
    setBusy(true);setError('');
    try {
      const value=await api.saveSettings(draft);
      saved(value);close();
    }catch(e){setError(describeError(e));}
    finally{setBusy(false);}
  }
  return <dialog className="settings-panel" ref={dialog} aria-labelledby="settings-title"
    onCancel={event=>{event.preventDefault();if(!busy)close();}}
    onClick={event=>{if(event.target===event.currentTarget && !busy)close();}}>
    <form onSubmit={event=>{event.preventDefault();void save();}}>
      <div className="settings-heading"><h2 id="settings-title">Settings</h2>
        <button type="button" className="icon-button" aria-label="Close settings" disabled={busy} onClick={close}><X size={19}/></button>
      </div>
      {loading && <p role="status">Loading settings…</p>}
      {settings && draft && !loading && <>
        {!settings.can_edit && <p className="notice">These settings are managed by your administrator.</p>}
        <fieldset disabled={busy || !settings.can_edit}>
          <legend>Review</legend>
          <label className="settings-field" htmlFor="settings-run-mode">Run mode
            <select id="settings-run-mode" aria-label="Run mode" value={draft.run_mode} onChange={e=>change({run_mode:e.target.value as SettingsUpdate['run_mode']})}>
              <option value="demo">Demo</option><option value="live">Live</option>
            </select>
          </label>
          <label className="settings-field" htmlFor="settings-core-model">Clinical review model
            <select id="settings-core-model" aria-label="Clinical review model" value={draft.core_model} onChange={e=>change({core_model:e.target.value})}>
              {!settings.available_models.includes(draft.core_model) && <option value={draft.core_model}>{draft.core_model} (unavailable)</option>}
              {settings.available_models.map(model=><option key={model} value={model}>{model}</option>)}
            </select>
          </label>
          {!settings.openai_configured && <p className="meta">Live mode needs an OpenAI key configured on the server.</p>}
        </fieldset>
        <fieldset disabled={busy || !settings.can_edit}>
          <legend>Features</legend>
          {featureLabels.map(feature=><label className="settings-feature" key={feature.key}>
            <span><strong>{feature.title}</strong><span className="meta"> · {feature.description}</span></span>
            <input type="checkbox" role="switch" aria-label={feature.title} checked={Boolean(draft.features[feature.key])}
              onChange={e=>change({features:{...draft.features,[feature.key]:e.target.checked}})}/>
          </label>)}
          {draft.features.classification && !settings.classification_configured && <p className="notice">Configure the JEV key on the server before enabling classification.</p>}
        </fieldset>
        <section className="settings-access" aria-label="Access"><span>Access</span><strong>{accessLabels[settings.access_mode]}</strong></section>
      </>}
      {error && <div className="error" role="alert"><p>{error}</p><button type="button" disabled={busy} onClick={()=>setAttempt(n=>n+1)}>Reload settings</button></div>}
      <div className="settings-footer">{!changed && <button type="button" disabled={busy} onClick={close}>Close</button>}
        {settings?.can_edit && changed && <button type="submit" className="primary" disabled={busy || loading || !draft}>{busy?'Saving…':'Save'}</button>}
      </div>
    </form>
  </dialog>;
}
