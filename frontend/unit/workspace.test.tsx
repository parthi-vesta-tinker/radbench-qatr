// DOM/state tests use API doubles. They do not exercise or simulate clinical AI quality.
import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { act } from 'react';
import App from '../src/App';
import { api, ApiError } from '../src/api';
import type { Review } from '../src/types';
import type { Analytics, KnowledgeCatalog, KnowledgeDetail, KnowledgeDraftInput } from '../src/types';
import type { PlaygroundCatalog, PlaygroundRun } from '../src/types';
const window = new Window({url:'http://localhost:8000'});
Object.assign(globalThis, {window, document:window.document, HTMLElement:window.HTMLElement,
  InputEvent:window.InputEvent, sessionStorage:window.sessionStorage, localStorage:window.localStorage, IS_REACT_ACT_ENVIRONMENT:true});
const {createRoot} = await import('react-dom/client');
let root: ReturnType<typeof createRoot>;
let requests: {text:string; key:string}[];
const results = new Map<string, Review>();
function review(id:string,text:string): Review { return {id,object:'qa_review', tenant_id:'vesta',api_version:'2026-09-22',input:{report_text:text},input_version:1,created_at:new Date().toISOString(),input_hash:'test',execution_status:'failed',steps:[],result:null,error:null,provenance:{mode:'openai',policy_status:'provisional_no_manual'}}; }
function button(name: string) { const node=[...document.querySelectorAll('button')].find(el=>el.getAttribute('aria-label')===name || el.textContent?.trim()===name); assert.ok(node, `Missing button: ${name}`); return node as HTMLButtonElement; }
async function click(name:string) { await act(async()=>{button(name).click();}); }
async function paste(text:string) { await act(async()=>{const input=document.querySelector('#report-text') as HTMLTextAreaElement; assert.ok(input && !input.readOnly); Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value')!.set!.call(input,text);input.dispatchEvent(new window.Event('input',{bubbles:true}));}); }
async function mount() {await act(async()=>{root.render(<App/>);});}
const text = () => (document.querySelector('#report-text') as HTMLTextAreaElement).value;
const analytics = (): Analytics => ({object:'qa_analytics',tenant_id:'vesta',checked_at:new Date().toISOString(),period:'7d',period_start:null,source:'openai',reviews:{total:0,with_comments:0,no_comments:0,critical:0,statuses:{queued:0,running:0,completed:0,needs_input:0,failed:0}},feedback:{total:0,reviews:0,up:0,down:0,reasons:{}},critical_evaluation:{status:'not_measured',precision:null,recall:null,false_positive_rate:null,false_alert_share:null,reason:'No adjudicated reference cohort.'}});
const knowledgeDetail = (): KnowledgeDetail => ({document:{document_id:'skill_test',title:'Review instructions',kind:'skill',description:'Controlled editorial content.',source_path:'skills/test/SKILL.md',version:'0.2.0',source_sha256:'a'.repeat(64),stages:['critical_finding_review'],used_by:['test'],runtime_use:'model_instruction',latest_revision:0,has_changes:false,source_changed:false},package_sha256:'b'.repeat(64),installed_content:'Installed instructions.',draft:null,saved_diff:'',recent_revisions:[],history_truncated:false});
const playgroundCatalog = (mode:'demo'|'openai'='openai'): PlaygroundCatalog => ({object:'qa_playground_catalog',mode,ready:true,models:['gpt-6-astra'],live_model:'configured-model',pack_version:'0.3.0',pack_release:'vesta-qatr-0.3.0',skills:['a','b'],boundary:'Playground output is not a clinical review.',
  categories:[{id:'critical_finding',title:'Critical findings',description:'Reports containing a critical observation.'},{id:'inconsistency',title:'Findings and impression inconsistency',description:'Impression does not follow from findings.'}],
  samples:[{sample_id:'critical-flagged',category:'critical_finding',title:'Flagged critical',report_text:'Findings:\nAcute right pneumothorax.\nImpression:\nAcute right pneumothorax.',demo_supported:true},
           {sample_id:'critical-uncertain',category:'critical_finding',title:'Uncertain critical',report_text:'Findings:\nPossible bleed.\nImpression:\nUncertain.',demo_supported:false},
           {sample_id:'laterality-swap',category:'inconsistency',title:'Laterality swap',report_text:'Findings:\nLeft effusion.\nImpression:\nRight effusion.',demo_supported:true}]});
const playgroundRun = (status:PlaygroundRun['status'],extra:Partial<PlaygroundRun>={}): PlaygroundRun => ({object:'qa_playground_run',run_id:'pg_controlled',release_id:'vesta-qatr-0.3.0',pack_ref:'published',source:'sample',sample_id:'critical-flagged',report_text:'Findings: x',model:'gpt-6-astra',mode:'openai',status,created_at:new Date().toISOString(),completed_at:null,
  steps:[{step:'input_validation',status:'completed',elapsed_ms:12},{step:'combined_review',status:status==='completed'?'completed':'running',elapsed_ms:status==='completed'?2400:null},{step:'output_validation',status:status==='completed'?'completed':'queued',elapsed_ms:null},{step:'comment_assembly',status:status==='completed'?'completed':'queued',elapsed_ms:null}],
  result:status==='completed'?{outcome:'observations',general_comments:[{observation_id:'o1',comment:'Controlled general comment.'}],critical_comments:[{observation_id:'o2',comment:'Controlled critical comment.'}]}:null,error:null,...extra});
const knowledgeCatalog = (): KnowledgeCatalog => ({package_version:'0.2.0',package_sha256:'b'.repeat(64),can_edit:true,items:[knowledgeDetail().document]});
async function field(id:string,value:string) {await act(async()=>{const input=document.getElementById(id)!;const prototype=input.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(prototype,'value')!.set!.call(input,value);input.dispatchEvent(new window.Event('input',{bubbles:true}));});}
async function choose(label:string,value:string) { await act(async()=>{const select=[...document.querySelectorAll('label')].find(n=>n.textContent?.startsWith(label))?.querySelector('select');assert.ok(select);select.value=value;select.dispatchEvent(new window.Event('change',{bubbles:true}));}); }
beforeEach(()=>{
  sessionStorage.clear();localStorage.clear();results.clear();requests=[];
  document.body.innerHTML='<div id="root"></div>';root=createRoot(document.getElementById('root')!);
  api.config=async()=>({tenant_id:'vesta',api_version:'2026-09-22',mode:'openai',ready:true,model:'configured-model',policy_status:'provisional_no_manual',samples:[]});
  api.status=async()=>({status:'ready',checked_at:new Date().toISOString(),readiness_scope:'Local checks only',components:{api:{status:'ok',message:'API responds'},dbos:{status:'ok',message:'Checkpoint store responds'},openai:{status:'configured',message:'Inference not verified'}}});
  api.history=async()=>({items:[],has_more:false,next_cursor:null});
  api.feedbackInbox=async()=>({items:[],has_more:false,next_cursor:null});
  api.analytics=async()=>analytics();
  api.knowledgeCatalog=async()=>knowledgeCatalog();
  api.knowledgeDetail=async()=>knowledgeDetail();
  api.playground=async()=>playgroundCatalog();
  api.startPlaygroundRun=async()=>playgroundRun('running');
  api.playgroundRun=async()=>playgroundRun('completed');
  window.confirm=()=>false;
  api.get=async(id)=>{const r=results.get(id);assert.ok(r);return r;};
  api.replace=async(id,text,version,key)=>{requests.push({text,key});const r={...review(id,text),input_version:version+1};results.set(id,r);return r;};
  api.create=async(input,key)=>{requests.push({text:input.report_text,key});const r=review('qr-'+requests.length,input.report_text);results.set(r.id,r);return r;};
});
afterEach(async()=>{await act(async()=>root.unmount());});
test('Current review is the only unfinished entry and New review preserves its text',async()=>{
  await mount();await paste('first input');await click('New review');await click('New review');
  assert.equal(text(),'first input');
  assert.equal(document.querySelectorAll('.draft-row').length,0);
  assert.equal(document.querySelector('[aria-label="Delete draft 1"]'),null);
  assert.equal(document.querySelector('.undo-bar'),null);
  await click('Review history');await click('Current review');assert.equal(text(),'first input');
});
test('New review remains usable when selected repeatedly with no text',async()=>{
  await mount();await click('New review');await click('New review');assert.equal(text(),'');
  await paste('one report');await click('Review');assert.equal(requests.length,1);
});
test('submitted input stays editable and new work can proceed',async()=>{
  await mount();await paste('Findings: source A. Impression: source A.');await click('Review');
  // A submitted report is editable; reviewing again is a new review, never a mutation.
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,false);
  assert.equal(button('Review again').disabled,false);
  await click('New review');await paste('Findings: source B. Impression: source B.');await click('Review');
  assert.equal(requests.length,2);assert.notEqual(requests[0].key,requests[1].key);
});
test('editing a submitted report enables Review again and updates the same review',async()=>{
  await mount();await paste('Findings: original. Impression: original.');await click('Review');
  assert.equal(requests.length,1);
  await paste('Findings: corrected. Impression: corrected.');
  assert.equal(button('Review again').disabled,false);
  await click('Review again');
  assert.equal(requests.length,2);
  assert.equal(requests[1].text,'Findings: corrected. Impression: corrected.');
  assert.notEqual(requests[0].key,requests[1].key);
  // The first review keeps the text it was accepted with.
  assert.equal(results.size,1);
  assert.equal(results.get('qr-1')!.input.report_text,'Findings: corrected. Impression: corrected.');
  assert.equal(document.querySelectorAll('.draft-row').length,0);
});
test('New review keeps an in-flight submission until acceptance',async()=>{
  let accept!:(r:Review)=>void;
  api.create=()=>new Promise(resolve=>{accept=resolve;});
  await mount();await paste('first input');await click('Review');
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,true);
  await click('New review');assert.equal(text(),'first input');
  const r=review('qr-late','first input');results.set(r.id,r);
  await act(async()=>accept(r));assert.equal(text(),'first input');assert.equal(document.querySelectorAll('.draft-row').length,0);
});
test('ambiguous network failure locks input and retries the identical operation',async()=>{
  let calls=0;
  api.create=async(input,key)=>{requests.push({text:input.report_text,key});if(calls++===0)throw new ApiError(0,'QA_CONNECTION_FAILED','Connection lost');const r=review('qr-retry',input.report_text);results.set(r.id,r);return r;};
  await mount();await paste('immutable request');await click('Review');
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,true);
  await click('New review');assert.equal(text(),'immutable request');
  await click('Retry submission');assert.equal(requests.length,2);assert.deepEqual(requests[0],requests[1]);
});
test('theme persists and environment controls and canned input controls are absent',async()=>{
  await mount();await click('Switch to dark theme');assert.equal(document.documentElement.dataset.theme,'dark');assert.equal(localStorage.getItem('vesta.theme'),'dark');
  await click('Switch to light theme');assert.equal(document.documentElement.dataset.theme,'light');
  assert.equal(document.querySelector('[aria-label="Execution mode for new reviews"]'),null);assert.equal(document.querySelector('[aria-label="Load synthetic example"]'),null);
});
test('health reports unavailable truthfully and dismisses on every route',async()=>{
  api.status=async()=>{throw new ApiError(0,'QA_CONNECTION_FAILED','Service unavailable');};
  await mount();const summary=document.querySelector('.health-trigger')!;assert.match(summary.getAttribute('aria-label')!,/Unavailable/);
  const panel=document.querySelector('.health-panel') as HTMLDivElement;
  const open=async()=>act(async()=>{(summary as HTMLButtonElement).click();});
  // The close button exists and dismisses the panel.
  await open();assert.equal(panel.hidden,false);
  await click('Close service health');assert.equal(panel.hidden,true);
  // Escape works wherever focus sits, not only on the summary.
  await open();
  await act(async()=>{document.dispatchEvent(new window.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));});
  assert.equal(panel.hidden,true);
  // An outside pointer press dismisses it.
  await open();
  await act(async()=>{document.querySelector('.brand')!.dispatchEvent(new window.MouseEvent('pointerdown',{bubbles:true}));});
  assert.equal(panel.hidden,true);
  // The double-click force-open is gone: a dblclick no longer holds it open.
  await act(async()=>summary.dispatchEvent(new window.MouseEvent('dblclick',{bubbles:true})));
  assert.equal(panel.hidden,true);
});
test('Studio navigation preserves report input and exposes distinct tools',async()=>{
  await mount();await paste('draft to preserve');await click('Review history');await click('Current review');assert.equal(text(),'draft to preserve');
  await click('Feedbacks');assert.match(document.querySelector('.history-pane h1')!.textContent!,/Feedbacks/);
  await click('Analytics');assert.match(document.querySelector('.history-pane')!.textContent!,/Not measured/);
  await click('Current review');assert.equal(text(),'draft to preserve');
});

test('feedback inbox reads notes and opens associated report without losing draft',async()=>{
  const r=review('qr-feedback','Associated report');results.set(r.id,r);
  api.feedbackInbox=async query=>{assert.equal(new URLSearchParams(query).get('rating'),'down');return {items:[{feedback:{id:'qf-1',review_id:r.id,created_at:new Date().toISOString(),result_version:1,rating:'down',target:'result',reason:'unclear_wording',explanation:'Make the comment shorter.'},report_preview:'Associated report',source:'openai',target_comment:null}],has_more:false,next_cursor:null};};
  await mount();await paste('preserved draft');await click('Feedbacks');
  assert.match(document.querySelector('.inbox-list')!.textContent!,/Make the comment shorter/);
  await click('Open report');assert.equal(text(),'Associated report');await click('Current review');assert.equal(text(),'preserved draft');
});

test('feedback inbox filters and request errors are recoverable',async()=>{
  const queries:string[]=[];let fail=true;
  api.feedbackInbox=async query=>{queries.push(query);if(fail)throw new ApiError(503,'UNAVAILABLE','Try later');return {items:[],has_more:false,next_cursor:null};};
  await mount();await click('Feedbacks');assert.match(document.querySelector('[role="alert"]')!.textContent!,/Try later/);
  fail=false;await click('Retry feedback');assert.match(document.querySelector('.feedback-inbox')!.textContent!,/No feedback matches/);
  await choose('Rating','');await choose('Reason','missed_observation');
  const last=new URLSearchParams(queries.at(-1));assert.equal(last.get('reason'),'missed_observation');assert.equal(last.has('rating'),false);
});

test('feedback inbox paginates once per entry and resets on filter change',async()=>{
  const item=(id:string)=>({feedback:{id:id,review_id:'qr-inbox',created_at:new Date().toISOString(),result_version:1,rating:'down' as const,target:'result' as const,reason:'unclear_wording',explanation:id},report_preview:'Controlled report context',source:'openai',target_comment:null});
  const queries:string[]=[];
  api.feedbackInbox=async query=>{queries.push(query);return new URLSearchParams(query).has('starting_after') ? {items:[item('qf-2'),item('qf-1')],has_more:false,next_cursor:null} : {items:[item('qf-2')],has_more:true,next_cursor:'qf-2'};};
  await mount();await click('Feedbacks');await click('Load more feedback');
  assert.equal(document.querySelectorAll('.inbox-list > li').length,2);
  assert.equal(new URLSearchParams(queries.at(-1)).get('starting_after'),'qf-2');
  await choose('Source','all');
  assert.equal(document.querySelectorAll('.inbox-list > li').length,1);
  assert.equal(new URLSearchParams(queries.at(-1)).has('starting_after'),false);
});

test('analytics uses service totals and preserves unknown clinical performance',async()=>{
  api.analytics=async()=>({...analytics(),reviews:{...analytics().reviews,total:237}});
  await mount();await click('Analytics');const pane=document.querySelector('.operational-analytics')!;
  assert.match(pane.textContent!,/237/);assert.doesNotMatch(pane.textContent!,/stakeholders accepting/);
  // Unmeasured clinical performance stays visible as a section-level verdict...
  const critical=pane.querySelector('[aria-label="Critical finding performance"]')!;
  assert.match(critical.querySelector('.section-status')!.textContent!,/Not measured/);
  // ...and all four measures keep their distinct denominators and their null result.
  const measures=critical.querySelectorAll('.measurement-list > div');
  assert.equal(measures.length,4);
  assert.ok([...measures].every(el=>/Not measured/.test(el.textContent!)));
  for (const formula of ['TP / (TP + FN)','TP / (TP + FP)','FP / (FP + TN)','FP / (TP + FP)']) {
    assert.ok(critical.textContent!.includes(formula),`Missing denominator: ${formula}`);
  }

});

test('late analytics response cannot replace a new period',async()=>{
  let release!:(value:Analytics)=>void;
  api.analytics=query=>new URLSearchParams(query).get('period')==='7d' ? new Promise(resolve=>{release=resolve;}) : Promise.resolve({...analytics(),period:'30d',reviews:{...analytics().reviews,total:300}});
  await mount();await click('Analytics');await choose('Period','30d');
  await act(async()=>release({...analytics(),reviews:{...analytics().reviews,total:999}}));
  const totals=document.querySelector('[aria-label="Review totals"]')!.textContent!;assert.match(totals,/300/);assert.doesNotMatch(totals,/999/);
});

test('Studio skills editor preserves unsaved edits across report navigation',async()=>{
  await mount();await paste('Report draft stays intact');await click('Skills');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Installed instructions.');
  await field('knowledge-content','Proposed instructions.');
  await click('Compare with installed');
  assert.equal(document.querySelectorAll('.knowledge-content textarea').length,2);
  await click('Current review');assert.equal(text(),'Report draft stays intact');
  await click('Skills');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Proposed instructions.');
  await click('Reload source');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Proposed instructions.'); // declined discard
});

test('draft save retry is idempotent and never changes installed content',async()=>{
  const calls:{payload:KnowledgeDraftInput;key:string}[]=[];
  api.saveKnowledgeDraft=async(id,payload,key)=>{calls.push({payload,key});if(calls.length===1)throw new ApiError(0,'LOST','Confirmation lost');return {...payload,draft_id:'kd-1',document_id:id,revision:1,content_sha256:'c'.repeat(64),created_at:new Date().toISOString(),status:'draft_not_active'};};
  await mount();await click('Skills');await field('knowledge-content','Proposed instruction');await field('knowledge-note','Clarify behavior');
  await click('Save draft');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,true);
  await click('Retry same save');assert.deepEqual(calls[0],calls[1]);
  assert.match(document.querySelector('.knowledge-pane')!.textContent!,/Draft revision 1 saved/);
  await click('Compare with installed');
  assert.equal((document.querySelector('.knowledge-content textarea[readonly]') as HTMLTextAreaElement).value,'Installed instructions.');
});

test('editor permissions and unavailable catalog are explicit',async()=>{
  let fail=true;api.knowledgeCatalog=async()=>{if(fail)throw new ApiError(503,'SOURCE_UNAVAILABLE','Source unavailable');return {...knowledgeCatalog(),can_edit:false};};
  await mount();await click('Skills');assert.match(document.querySelector('.knowledge-pane [role="alert"]')!.textContent!,/Source unavailable/);
  fail=false;await click('Retry catalog');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,true);
  assert.equal(document.querySelector('#knowledge-note'),null);
});

test('revision conflict retains text for reconciliation',async()=>{
  api.saveKnowledgeDraft=async()=>{throw new ApiError(409,'KNOWLEDGE_REVISION_CONFLICT','A newer draft exists.');};
  await mount();await click('Skills');await field('knowledge-content','Keep this proposal.');await field('knowledge-note','Reason');await click('Save draft');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Keep this proposal.');
  assert.match(document.querySelector('.knowledge-pane [role="alert"]')!.textContent!,/A newer draft exists/);
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,false);
});

test('playground runs a sample and shows results and phase logs without copy actions',async()=>{
  await mount();await click('Playground');
  const pane=()=>document.querySelector('.playground-pane')!;
  assert.match(pane().textContent!,/not a clinical review/i);
  assert.match(pane().textContent!,/Critical findings/);
  assert.match(pane().textContent!,/Findings and impression inconsistency/);
  assert.equal(button('Run test review').disabled,true);
  await click('Flagged criticalRuns in demo');
  assert.equal(button('Run test review').disabled,false);
  await click('Run test review');
  await act(async()=>{await new Promise(r=>setTimeout(r,1100));});
  const log=[...pane().querySelectorAll('.playground-log li')].map(n=>n.textContent);
  assert.equal(log.length,4);
  assert.match(log[0]!,/Input validation/);
  assert.match(log[1]!,/Combined report review/);
  assert.match(pane().textContent!,/Controlled general comment/);
  assert.match(pane().textContent!,/Controlled critical comment/);
  // A playground comment must not be copyable into a real report.
  assert.equal([...pane().querySelectorAll('button')].filter(b=>/copy/i.test(b.textContent??'')).length,0);
});

test('demo mode blocks samples it cannot serve and the playground never enters history',async()=>{
  api.playground=async()=>playgroundCatalog('demo');
  await mount();await click('Playground');
  await click('Uncertain criticalNeeds a model');
  assert.equal(button('Run test review').disabled,true);
  assert.match(document.querySelector('.playground-pane')!.textContent!,/needs a configured model/i);
  await click('Review history');
  assert.equal(document.querySelector('.playground-pane')!.hasAttribute('hidden'),true);
  assert.equal(requests.length,0);
});

test('review history filters by submission time and opens comments without opening the report',async()=>{
  const row={id:'qr-history-abcde',display_id:'ABCDE',created_at:new Date().toISOString(),submitted_by:null,execution_status:'completed',preview:'Findings: controlled history report. Impression: controlled.',outcome:'observations',general_count:1,critical_count:0,feedback_count:0,mode:'demo'};
  const queries:string[]=[];
  api.history=async query=>{queries.push(query);return {items:[row],has_more:false,next_cursor:null};};
  api.comments=async id=>({review_id:id,execution_status:'completed',result_version:1,general_comments:[{observation_id:'obs-1',finding_type:'suggestion',report_section:'findings',comment:'Controlled PACS comment.'}],critical_comments:[]});
  await mount();await click('Review history');
  assert.match(document.querySelector('.history-pane')!.textContent!,/ABCDE/);
  assert.match(document.querySelector('.history-pane')!.textContent!,/Not recorded/);
  await choose('Submitted','24h');
  assert.ok(new URLSearchParams(queries.at(-1)).has('submitted_after'));
  await choose('Results','general');
  assert.equal(new URLSearchParams(queries.at(-1)).get('comment_type'),'general');
  await choose('Results','any');
  assert.equal(new URLSearchParams(queries.at(-1)).has('comment_type'),false);
  await choose('Feedback','false');
  assert.equal(new URLSearchParams(queries.at(-1)).get('has_feedback'),'false');
  await choose('Feedback','any');
  assert.equal(new URLSearchParams(queries.at(-1)).has('has_feedback'),false);
  await choose('Status','failed');
  assert.equal(new URLSearchParams(queries.at(-1)).get('status_group'),'failed_or_needs_input');
  const statusSelect=[...document.querySelectorAll('label')].find(label=>label.textContent?.startsWith('Status'))?.querySelector('select');
  assert.ok(statusSelect);
  const statusOptions=[...statusSelect.options].map(option=>option.value);
  assert.deepEqual(statusOptions,['','completed','failed']);
  await click('1 PACS · 0 critical');
  assert.match(document.querySelector('.history-modal')!.textContent!,/Controlled PACS comment/);
  assert.equal(document.querySelector('#report-text')?.getAttribute('value'),null);
  await click('Close history dialog');
});

test('panel preferences preserve drafts and unsaved Skills content',async()=>{
  window.happyDOM.setWindowSize({width:1536,height:1024});
  await mount();await paste('Keep the report');await click('Skills');
  await field('knowledge-content','Keep this unsaved edit');
  await click('Collapse Report reviews');await click('Collapse QA Studio');
  assert.equal(button('Expand Report reviews').getAttribute('aria-expanded'),'false');
  assert.equal(button('Expand QA Studio').getAttribute('aria-expanded'),'false');
  await click('Current review');assert.equal(text(),'Keep the report');
  await click('Skills');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Keep this unsaved edit');
  await click('Expand QA Studio');
  assert.deepEqual(JSON.parse(localStorage.getItem('vesta.panels.v1')!),{reports:true,studio:false});
});

test('collapsed tooltips appear on focus and dismiss with Escape',async()=>{
  window.happyDOM.setWindowSize({width:1536,height:1024});
  await mount();await click('Collapse QA Studio');
  await act(async()=>{button('Skills').focus();});
  const id=button('Skills').getAttribute('aria-describedby');assert.ok(id);
  assert.equal(document.getElementById(id)?.textContent,'Skills');
  await act(async()=>{document.dispatchEvent(new window.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));});
  assert.equal(button('Skills').getAttribute('aria-describedby'),null);
  assert.equal(document.activeElement,button('Skills'));
});
