import { useEffect, useRef, useState } from 'react';
import { api, ApiError, describeError } from './api';
import type { KnowledgeCatalog, KnowledgeDetail, KnowledgeDraftInput } from './types';

const stages: Record<string,string> = {combined_review:'Combined report review', language_review:'Language', consistency_review:'Consistency', critical_finding_review:'Critical findings'};
const kinds: Record<string,string> = {skill:'Skill', reference:'Reference', guidance:'Local guidance', catalog:'Draft catalog', policy_source:'Source wording'};

export function SkillsKnowledge({active}: {active:boolean}) {
  const [catalog,setCatalog] = useState<KnowledgeCatalog|null>(null);
  const [selected,setSelected] = useState('');
  const [filter,setFilter] = useState('all');
  const [search,setSearch] = useState('');
  const [detail,setDetail] = useState<KnowledgeDetail|null>(null);
  const [content,setContent] = useState('');
  const [note,setNote] = useState('');
  const [compare,setCompare] = useState(false);
  const [loading,setLoading] = useState(false);
  const [saving,setSaving] = useState(false);
  const [retry,setRetry] = useState(false);
  const [refresh,setRefresh] = useState(0);
  const [catalogRefresh,setCatalogRefresh] = useState(0);
  const [catalogError,setCatalogError] = useState('');
  const [error,setError] = useState('');
  const [message,setMessage] = useState('');
  const [exporting,setExporting] = useState(false);
  const pending = useRef<{id:string; payload:KnowledgeDraftInput; key:string}|null>(null);
  const savedText = detail?.draft?.content ?? detail?.installed_content ?? '';
  const dirty = !!detail && (content !== savedText || !!note.trim());
  const locked = saving || retry;
  useEffect(()=>{
    let stopped=false;
    setCatalogError('');
    api.knowledgeCatalog().then(data=>{if(!stopped){setCatalog(data);setSelected(old=>old || data.items[0]?.document_id || '');}})
      .catch(e=>{if(!stopped)setCatalogError(describeError(e));});
    return ()=>{stopped=true;};
  },[catalogRefresh]);
  useEffect(()=>{
    if(!selected)return;
    let stopped=false;
    setLoading(true);setDetail(null);setError('');setMessage('');setNote('');
    api.knowledgeDetail(selected).then(data=>{if(!stopped){setDetail(data);setContent(data.draft?.content ?? data.installed_content);}})
      .catch(e=>{if(!stopped)setError(describeError(e));}).finally(()=>{if(!stopped)setLoading(false);});
    return ()=>{stopped=true;};
  },[selected,refresh]);
  useEffect(()=>{
    if(!dirty && !locked)return;
    const warn=(e:BeforeUnloadEvent)=>{e.preventDefault();e.returnValue='';};
    window.addEventListener('beforeunload',warn);
    return ()=>window.removeEventListener('beforeunload',warn);
  },[dirty,locked]);
  function canLeave() {return !locked && (!dirty || window.confirm('Discard unsaved skill edits? Saved revisions remain available.'));}
  function select(id:string) {if(id!==selected && canLeave())setSelected(id);}
  function reload() {if(canLeave()){setRefresh(n=>n+1);setCatalogRefresh(n=>n+1);}}
  async function save() {
    if(!detail || !catalog?.can_edit || saving || !content.trim() || !note.trim())return;
    pending.current ??= {id:selected,key:crypto.randomUUID(),payload:{expected_revision:detail.document.latest_revision ?? 0,source_sha256:detail.document.source_sha256,package_sha256:detail.package_sha256,content,change_note:note.trim()}};
    setSaving(true);setError('');setMessage('');
    try {
      const request=pending.current;
      const draft=await api.saveKnowledgeDraft(request.id,request.payload,request.key);
      pending.current=null;setRetry(false);setNote('');setContent(draft.content);
      // A successful save is authoritative even if a following catalog refresh fails.
      setDetail(old=>old ? {...old,draft,document:{...old.document,latest_revision:draft.revision,has_changes:draft.content_sha256!==old.document.source_sha256,source_changed:false},saved_diff:'',recent_revisions:[draft,...old.recent_revisions].slice(0,20)} : old);
      setCatalogRefresh(n=>n+1);setMessage(`Draft revision ${draft.revision} saved. Installed instructions remain active.`);
    } catch(e) {
      const uncertain=!(e instanceof ApiError) || e.status<400 || e.status>=500;
      if(!uncertain)pending.current=null;
      setRetry(uncertain);setError(describeError(e));
    } finally {setSaving(false);}
  }
  async function download(revision:number) {
    setExporting(true);setError('');
    try {
      const data=await api.exportKnowledgeDraft(selected,revision);
      const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}));
      const anchor=document.createElement('a');anchor.href=url;anchor.download=`${selected}-draft-r${revision}.json`;
      document.body.appendChild(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(e){setError(describeError(e));} finally{setExporting(false);}
  }
  const visible=catalog?.items.filter(item=>(filter==='all' || (filter==='skills' ? item.kind==='skill' : item.kind!=='skill')) && `${item.title} ${item.description}`.toLowerCase().includes(search.toLowerCase())) ?? [];
  return <main className="history-pane knowledge-pane" hidden={!active}>
    <div className="section-heading"><div><h1>Skills &amp; knowledge</h1><p className="meta">Review AI instructions and prepare changes</p></div><button onClick={reload} disabled={locked || loading}>Reload source</button></div>
    <p className="knowledge-boundary">Saved edits are drafts. Models continue using the installed package until an evaluated version is released.</p>
    {catalogError && <p className="error" role="alert">{catalogError} <button onClick={()=>setCatalogRefresh(n=>n+1)}>Retry catalog</button></p>}
    {!catalog && !catalogError && <p role="status">Loading skills…</p>}
    {catalog && <>
      <div className="history-filters"><label>Show<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All content</option><option value="skills">Skills</option><option value="knowledge">Knowledge base</option></select></label><label>Find content<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Name or purpose"/></label><span className="meta">Installed package {catalog.package_version}</span></div>
      <div className="knowledge-layout">
        <nav className="knowledge-list" aria-label="Skills and knowledge documents">
          {visible.map(item=><button key={item.document_id} aria-pressed={selected===item.document_id} disabled={locked} onClick={()=>select(item.document_id)}><strong>{item.title}</strong><span>{kinds[item.kind]} · {item.version}</span>{(item.latest_revision ?? 0)>0 && <span>{item.source_changed?'Source changed':item.has_changes?'Saved draft':'Draft matches source'} · r{item.latest_revision}</span>}</button>)}
          {!visible.length && <p className="meta">No matching content.</p>}
        </nav>
        <section className="knowledge-editor" aria-label="Knowledge editor" aria-busy={loading}>
          {loading && <p role="status">Loading document…</p>}
          {error && <p className="error" role="alert">{error}{!detail && <button onClick={()=>setRefresh(n=>n+1)}>Retry document</button>}</p>}
          {detail && <>
            <h2>{detail.document.title}</h2><p className="meta">{detail.document.description}</p>
            <p className="knowledge-usage">{detail.document.runtime_use==='host_reference' ? 'Host validation reference · This document is not sent to the model. Changing the deterministic gate also requires code changes.' : detail.document.runtime_use==='not_configured' ? 'Not configured · Prepare local guidance here for a future release.' : `Used in: ${detail.document.stages.map(stage=>stages[stage]??stage).join(' · ')}`}</p>
            {detail.document.source_changed && <p className="notice">The installed source changed since this draft was saved. Compare and reconcile the draft before saving a new revision.</p>}
            {!catalog.can_edit && <p className="notice">Read-only access. Editing requires skills:write permission.</p>}
            <div className="knowledge-toolbar"><button aria-pressed={compare} onClick={()=>setCompare(value=>!value)}>{compare?'Hide installed source':'Compare with installed'}</button><span className="meta">{dirty?'Unsaved changes':detail.draft?`Saved draft r${detail.draft.revision}`:'Installed source'}</span></div>
            <div className={'knowledge-content '+(compare?'comparing':'')}>
              {compare && <label>Installed content<textarea readOnly value={detail.installed_content} rows={20} spellCheck={false}/></label>}
              <label htmlFor="knowledge-content">{catalog.can_edit?'Draft content':'Content'}<textarea id="knowledge-content" readOnly={!catalog.can_edit || locked} value={content} onChange={e=>setContent(e.target.value)} maxLength={100000} rows={20} spellCheck={false}/></label>
            </div>
            {catalog.can_edit && <form onSubmit={e=>{e.preventDefault();void save();}}>
              <label htmlFor="knowledge-note">Change summary</label><input id="knowledge-note" value={note} onChange={e=>setNote(e.target.value)} maxLength={1000} disabled={locked} placeholder="What changed and why?" required/>
              <div className="knowledge-actions"><button className="primary" disabled={saving || !content.trim() || !note.trim() || (!dirty && !retry)}>{saving?'Saving…':retry?'Retry same save':'Save draft'}</button><button type="button" disabled={locked || !dirty} onClick={()=>{if(canLeave()){setContent(savedText);setNote('');setError('');}}}>Discard unsaved edits</button>{detail.draft && <button type="button" disabled={exporting} onClick={()=>void download(detail.draft!.revision)}>Export saved draft</button>}</div>
            </form>}
            {retry && <p className="meta">Save confirmation was lost. Retry uses the same revision and operation.</p>}
            {message && <p className="meta" role="status">{message}</p>}
            <details className="disclosure disclosure-section knowledge-history"><summary>Saved revisions ({detail.recent_revisions.length}{detail.history_truncated?'+':''})</summary>{detail.recent_revisions.length===0?<p className="meta">No draft revisions yet.</p>:<ol>{detail.recent_revisions.map(row=><li key={row.draft_id}><div><strong>Revision {row.revision}</strong><p>{row.change_note}</p><span className="meta">{new Date(row.created_at).toLocaleString()} · Draft, not active</span></div><button disabled={locked || !catalog.can_edit} onClick={()=>{if(canLeave()){setContent(row.content);setNote(`Restore revision ${row.revision}`);}}}>Use revision {row.revision}</button></li>)}</ol>}{detail.history_truncated && <p className="meta">Latest 20 revisions shown; older revisions remain stored and exportable by revision.</p>}</details>
            <details className="disclosure disclosure-section knowledge-history"><summary>Source &amp; release details</summary><p className="meta">{detail.document.source_path ?? 'Tenant-specific backend guidance; filesystem path is private.'}</p><p className="meta">Source SHA-256: {detail.document.source_sha256}</p><p className="meta">Framework contracts and host validation are code-managed. Export a saved proposal, review the change, update the affected skill/reference versions and evaluations, and release a validated package. Existing reviews retain their captured instructions.</p></details>
          </>}
        </section>
      </div>
    </>}
  </main>;
}
