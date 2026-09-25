// DOM/state tests use API doubles. They do not exercise or simulate clinical AI quality.
import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { act, useState } from 'react';
import { ReviewOutput } from '../src/ReviewOutput';
import App from '../src/App';
import { useClassification } from '../src/useClassification';
import { ReviewJourney } from '../src/ReviewJourney';
import { FindingClassification } from '../src/FindingClassification';
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
const analytics = (): Analytics => ({object:'qa_analytics',tenant_id:'vesta',checked_at:new Date().toISOString(),period:'24h',period_start:null,source:'all',reviews:{total:0,with_comments:0,no_comments:0,critical:0,statuses:{queued:0,running:0,completed:0,needs_input:0,failed:0}},findings:{inconsistencies:0,critical_findings:0,clinical_observations:0,other_issues:0},feedback:{total:0,reviews:0,up:0,down:0,reasons:{}},critical_evaluation:{status:'not_measured',precision:null,recall:null,false_positive_rate:null,false_alert_share:null,reason:'No adjudicated reference cohort.'}});
const knowledgeDetail = (): KnowledgeDetail => ({document:{document_id:'skill_test',title:'Review instructions',kind:'skill',description:'Controlled editorial content.',source_path:'skills/test/SKILL.md',version:'0.2.0',source_sha256:'a'.repeat(64),stages:['critical_finding_review'],used_by:['test'],runtime_use:'model_instruction',latest_revision:0,has_changes:false,source_changed:false},package_sha256:'b'.repeat(64),installed_content:'Installed instructions.',draft:null,saved_diff:'',recent_revisions:[],history_truncated:false});
const playgroundCatalog = (mode:'demo'|'live'='live'): PlaygroundCatalog => ({object:'qa_playground_catalog',run_mode:mode,ready:true,models:['gpt-6-astra'],live_model:'configured-model',pack_version:'0.3.0',pack_release:'vesta-qatr-0.3.0',skills:['a','b'],boundary:'Playground output is not a clinical review.',
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
async function choosePeriod(value:Analytics['period']) { await act(async()=>{const select=document.querySelector('#analytics-period') as HTMLSelectElement;assert.ok(select);select.value=value;select.dispatchEvent(new window.Event('change',{bubbles:true}));}); }
beforeEach(()=>{
  sessionStorage.clear();localStorage.clear();results.clear();requests=[];
  document.body.innerHTML='<div id="root"></div>';root=createRoot(document.getElementById('root')!);
  api.config=async()=>({tenant_id:'vesta',api_version:'2026-09-22',run_mode:'live',features:{playground:true,skills:true,classification:true},ready:true,model:'configured-model',policy_status:'provisional_no_manual',samples:[]});
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
  await click('Close application health');assert.equal(panel.hidden,true);
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
  await click('Analytics');assert.match(document.querySelector('.history-pane')!.textContent!,/Review findings/);
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

test('analytics shows saved finding counts and uses the selected period across sources',async()=>{
  const queries:string[]=[];
  api.analytics=async query=>{queries.push(query);return {...analytics(),reviews:{...analytics().reviews,total:237},findings:{inconsistencies:8,critical_findings:3,clinical_observations:2,other_issues:4}};};
  await mount();await click('Analytics');const pane=document.querySelector('.operational-analytics')!;
  assert.match(pane.querySelector('[aria-label="Review findings"]')!.textContent!,/Inconsistencies8Critical findings3Clinical observations2Other issues4/);
  assert.match(pane.querySelector('[aria-label="Review activity"]')!.textContent!,/Submitted237/);
  assert.equal(pane.querySelectorAll('select').length,1);
  assert.equal(new URLSearchParams(queries.at(-1)).get('source'),'all');
  assert.equal(new URLSearchParams(queries.at(-1)).get('period'),'24h');
  await choosePeriod('1h');
  assert.equal(new URLSearchParams(queries.at(-1)).get('period'),'1h');
  assert.doesNotMatch(pane.textContent!,/precision|recall|feedback totals/i);
});

test('late analytics response cannot replace a new period',async()=>{
  let release!:(value:Analytics)=>void;
  api.analytics=query=>new URLSearchParams(query).get('period')==='24h' ? new Promise(resolve=>{release=resolve;}) : Promise.resolve({...analytics(),period:'30d',reviews:{...analytics().reviews,total:300}});
  await mount();await click('Analytics');await choosePeriod('30d');
  await act(async()=>release({...analytics(),reviews:{...analytics().reviews,total:999}}));
  const totals=document.querySelector('[aria-label="Review activity"]')!.textContent!;assert.match(totals,/300/);assert.doesNotMatch(totals,/999/);
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
  assert.doesNotMatch(pane().textContent!,/not a clinical review/i);
  assert.match(pane().textContent!,/Critical findings/);
  assert.match(pane().textContent!,/Findings & impression/);
  await click('Flagged critical finding');
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
  await click('Uncertain critical concernModel required');
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
  const headers=[...document.querySelectorAll('.review-history-table th')].map(header=>header.textContent);
  assert.deepEqual(headers,['Review ID','Report description','Submitted by','Submitted time','Status','Comments','Classification','Feedback']);
  assert.equal(document.querySelector('.history-status')?.textContent,'Completed');
  await choose('Submitted','24h');
  assert.ok(new URLSearchParams(queries.at(-1)).has('submitted_after'));
  await click('1 PACS · 0 critical');
  assert.match(document.querySelector('.history-modal')!.textContent!,/Controlled PACS comment/);
  assert.equal(document.querySelector('#report-text')?.getAttribute('value'),null);
  await click('Close history dialog');
});

test('review history uses one neutral status label style',async()=>{
  const base={created_at:new Date().toISOString(),submitted_by:null,preview:'Findings: controlled history report. Impression: controlled.',outcome:null,general_count:0,critical_count:0,feedback_count:null,mode:'demo' as const};
  api.history=async()=>({items:[{...base,id:'qr-complete',display_id:'COMPLETE',execution_status:'completed'},{...base,id:'qr-failed',display_id:'FAILED',execution_status:'failed'}],has_more:false,next_cursor:null});
  await mount();await click('Review history');
  const statuses=[...document.querySelectorAll('.history-status')];
  assert.deepEqual(statuses.map(status=>status.textContent),['Completed','Failed']);
  assert.ok(statuses.every(status=>status.className==='history-status'));
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


test('playground filters samples and preserves pasted text across source switches',async()=>{
  await mount();await click('Playground');
  const pane=document.querySelector('.playground-pane')!;
  await act(async()=>{
    const input=pane.querySelector('[aria-label="Search samples"]') as HTMLInputElement;
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value')!.set!.call(input,'laterality');
    input.dispatchEvent(new window.Event('input',{bubbles:true}));
  });
  assert.equal(pane.querySelectorAll('.playground-sample').length,1);
  await click('Laterality mismatch');
  assert.match(pane.querySelector('.playground-report-text')!.textContent!,/Left effusion/);
  await click('Paste report');await field('playground-report','Findings: preserved. Impression: preserved.');
  await click('Sample reports');
  assert.match(pane.querySelector('.playground-report-text')!.textContent!,/Left effusion/);
  await click('Paste report');
  assert.equal((pane.querySelector('#playground-report') as HTMLTextAreaElement).value,'Findings: preserved. Impression: preserved.');
  let payload:unknown;
  api.startPlaygroundRun=async input=>{payload=input;return playgroundRun('completed');};
  await click('Run test review');
  assert.deepEqual(payload,{model:'gpt-6-astra',report_text:'Findings: preserved. Impression: preserved.'});
});

test('classification preview expands priority and all labels with feedback',async()=>{
  const source = {...review('qr-critical','Findings: Acute right pneumothorax. Impression: Same.'),
    execution_status:'completed',result:{critical_comments:[{observation_id:'obs-critical',comment:'Acute right pneumothorax.'}]}} as unknown as Review;
  const labels = {finding_group:'thoracic',polarity:'affirmed',certainty:'definite',temporal_status:'not_stated',urgency:'minutes'};
  const fields = Object.fromEntries(Object.entries(labels).map(([field,label])=>[field,{label,raw_probabilities:{[label]:1},
    provider_confidence:1,top_probability:1,margin:1,calibrated_probabilities:null,review_reasons:[]}])) as any;
  api.classificationConfig=async()=>({enabled:true,ready:true,reason:null,model:'jev-1.13.0',rubric_id:'finding-rubric-v1',
    rubric_hash:'hash',calibration_status:'uncalibrated',labels:Object.fromEntries(Object.entries(labels).map(([field,label])=>[field,[label]]))}) as any;
  api.classificationsForReview=async()=>[{id:'jc-1',object:'finding_classification',review_id:'qr-critical',input_version:1,
    observation_id:'obs-critical',input_hash:'hash',input:{finding_text:'Acute right pneumothorax.',qa_comment:'Acute right pneumothorax.',report_quotes:[]},
    source_status:'current',execution_status:'completed',steps:[],result:{fields,calibration_status:'uncalibrated',calibrator_id:null,human_review_required:true,usage:null,duration_ms:2},
    error:null,provenance:{model:'jev-1.13.0',rubric_id:'finding-rubric-v1',rubric_hash:'hash',workflow_version:'qa.finding.classify.v1'},
    created_at:new Date().toISOString(),updated_at:new Date().toISOString()}] as any;
  let feedback:any;
  api.classificationFeedback=async(_id,input)=>{feedback=input;return {} as any;};
  await act(async()=>{root.render(<FindingClassification review={source} stale={false}/>);});
  assert.match(document.body.textContent!,/Finding group.*Thoracic/);
  assert.match(document.querySelector('.classification-preview')!.textContent!,/PriorityMinutes/);
  await click('More details');
  assert.equal(button('Classification Overview').getAttribute('aria-expanded'),'true');
  assert.match(document.body.textContent!,/Polarity.*Affirmed/);
  assert.match(document.body.textContent!,/Temporal status.*Not stated/);
  await click('Something wrong?');
  await click('Accept');
  assert.equal(feedback.action,'accept');
});

test('Classification uses minimal empty states and clears the previous review immediately', async () => {
  api.classificationsForReview = async () => [];
  await mount();
  await click('Classification');
  assert.match(document.querySelector('.classification-pane')!.textContent!, /Review this report to see classification\./);
  await click('Current review');
  await paste('Findings: test. Impression: test.');
  await click('Review');
  await click('Classification');
  assert.match(document.querySelector('.classification-pane')!.textContent!, /No classification available\./);
  await click('New review');
  await click('Classification');
  assert.match(document.querySelector('.classification-pane')!.textContent!, /Review this report to see classification\./);
});


test('late classification responses cannot cross review or input-version boundaries', async () => {
  let finish: (value: any) => void = () => {};
  const source = {...review('qr-one','Findings: one. Impression: one.'), execution_status:'completed',
    result:{critical_comments:[{observation_id:'obs-one'}]}} as unknown as Review;
  api.classificationsForReview = async () => new Promise(resolve => { finish = resolve; });
  function Probe({value}: {value: Review | null}) {
    const data = useClassification(value, true, false);
    return <div id="classification-probe">{data.runs.map(run => run.id).join(',')}</div>;
  }
  await act(async () => { root.render(<Probe value={source}/>); });
  const oldResponse = finish;
  await act(async () => { root.render(<Probe value={{...source,input_version:2}}/>); });
  await act(async () => { oldResponse([{id:'old-classification',review_id:source.id,input_version:1,source_status:'current',observation_id:'obs-one',execution_status:'completed'}]); });
  assert.equal(document.querySelector('#classification-probe')!.textContent, '');
  await act(async () => { finish([{id:'new-classification',review_id:source.id,input_version:2,source_status:'current',observation_id:'obs-one',execution_status:'completed'}]); });
  assert.equal(document.querySelector('#classification-probe')!.textContent, 'new-classification');
  await act(async () => { root.render(<Probe value={null}/>); });
  assert.equal(document.querySelector('#classification-probe')!.textContent, '');
});

test('classification progress preserves completed Results on pending and failed classification', async () => {
  const source = {...review('qr-one','text'), execution_status:'completed'} as Review;
  const data = {runs:[],config:null,loading:true,error:'',refresh:()=>{}};
  const context = {hasText:true,pasted:false,uncertain:false,restore:()=>{},error:''};
  await act(async () => {root.render(<ReviewJourney review={source} edited={false} busy={false} disconnected={false} classificationEnabled classification={data} {...context}/>);});
  assert.equal(document.querySelectorAll('.review-journey .complete').length,4);
  assert.match(document.querySelector('.review-journey .current')!.textContent!,/Classification/);
  await act(async () => {root.render(<ReviewJourney review={source} edited={false} busy={false} disconnected={false} classificationEnabled classification={{...data,loading:false,runs:[{execution_status:'failed'} as any]}} {...context}/>);});
  assert.equal(document.querySelectorAll('.review-journey .complete').length,4);
  assert.match(document.querySelector('.review-journey .blocked')!.textContent!,/Classification/);
});

test('classification is not applicable only for a completed review with no critical findings', async () => {
  const source = {...review('qr-clean','text'), execution_status:'completed', result:{critical_comments:[]}} as unknown as Review;
  const renderJourney = async (value: Review, edited = false) => act(async () => {
    root.render(<ReviewJourney review={value} edited={edited} busy={false} disconnected={false} classificationEnabled hasText pasted={false} uncertain={false} restore={()=>{}} error=""/>);
  });
  await renderJourney(source);
  const stage = document.querySelector('.review-journey li:last-child')!;
  assert.equal(stage.className, 'not-applicable');
  assert.match(stage.textContent!, /not applicable — no critical findings reported/);
  assert.ok(stage.querySelector('.lucide-minus'));
  await renderJourney({...source,execution_status:'failed',result:null});
  assert.equal(stage.className, 'pending');
  await renderJourney(source, true);
  assert.equal(stage.className, 'pending');
  await renderJourney({...source,result:null});
  assert.equal(stage.className, 'unavailable');
});

test('review failures explain the stage that failed', async () => {
  const context = {hasText:true,pasted:false,uncertain:false,restore:()=>{},error:''};
  for (const [step, label] of [
    ['input_validation','Validate'], ['combined_review','AI review'],
    ['output_validation','Results'], ['comment_assembly','Results'],
  ] as const) {
    const source = {...review('qr-stage','Findings: x. Impression: x.'),
      error:{code:'REVIEW_FAILED',message:`Failure in ${label}.`,retryable:false},
      steps:[{step_id:step,status:'failed',started_at:null,completed_at:null}]} as Review;
    await act(async()=>root.render(<ReviewJourney review={source} edited={false} busy={false} disconnected={false} {...context}/>));
    const stage = document.querySelector('.review-journey li[aria-describedby="input-help"]')!;
    assert.match(stage.textContent!,new RegExp(label));
    assert.match(document.querySelector('#input-help[role="alert"]')!.textContent!,new RegExp(`Failure in ${label}`));
    assert.equal(document.querySelector('#input-help details'),null);
  }
});

test('configuration failures point to AI review before a review exists', async () => {
  let retries = 0;
  await act(async()=>root.render(<ReviewJourney review={null} edited={false} busy={false} disconnected={false}
    hasText={false} pasted={false} uncertain={false} restore={()=>{}} error=""
    configurationError="The skill package is invalid. [SKILL_CONFIGURATION_INVALID · HTTP 503 · req_test]"
    retryConfiguration={()=>{retries++;}}/>));
  const stage = document.querySelector('.review-journey li[aria-describedby="input-help"]')!;
  assert.match(stage.textContent!,/AI review/);
  assert.equal(stage.className,'blocked');
  assert.equal(document.querySelectorAll('.review-journey .complete').length,0);
  assert.match(document.querySelector('#input-help[role="alert"]')!.textContent!,/The skill package is invalid/);
  assert.doesNotMatch(document.querySelector('#input-help')!.textContent!,/SKILL_CONFIGURATION_INVALID|HTTP 503|req_test/);
  assert.equal(document.querySelector('#input-help details'),null);
  await act(async()=>(document.querySelector('#input-help button') as HTMLButtonElement).click());
  assert.equal(retries,1);
});

test('classification error stays under its stage without request diagnostics', async () => {
  const source = {...review('qr-critical','Findings: x. Impression: x.'),execution_status:'completed',
    result:{critical_comments:[{observation_id:'critical-1'}]}} as unknown as Review;
  const classification = {runs:[],config:null,loading:false,error:'Classification unavailable. [JEV_UNAVAILABLE · HTTP 503 · req_test]',refresh:()=>{}};
  await act(async()=>root.render(<ReviewJourney review={source} edited={false} busy={false} disconnected={false}
    hasText pasted={false} uncertain={false} restore={()=>{}} error="" classificationEnabled classification={classification}/>));
  assert.match(document.querySelector('.review-journey li[aria-describedby="input-help"]')!.textContent!,/Classification/);
  const message = document.querySelector('#input-help[role="alert"]')!;
  assert.match(message.textContent!,/Classification unavailable/);
  assert.doesNotMatch(message.textContent!,/JEV_UNAVAILABLE|HTTP 503|req_test/);
  assert.equal(message.querySelector('details'),null);
});

test('Recent keeps older pending reviews above recent results and selects only the opened report', async()=>{
  const saved = Array.from({length:20}, (_, i) => ({...review(`qr_saved_${i}`, `Saved report ${i}`), created_at:new Date(2026,8,24,12,i).toISOString()}));
  const queued = {...review('qr_queued','Older queued report'), execution_status:'queued' as const, created_at:'2026-09-01T00:00:00Z'};
  const running = {...review('qr_running','Running report'), execution_status:'running' as const, created_at:'2026-09-02T00:00:00Z'};
  [queued,running,...saved].forEach(r=>results.set(r.id,r));
  const summary = (r:Review) => ({id:r.id,display_id:r.id,created_at:r.created_at,submitted_by:null,execution_status:r.execution_status,outcome:null,general_count:0,critical_count:0,feedback_count:0,preview:r.input.report_text,mode:'openai'});
  api.history=async(query='')=>({items:(query.includes('status=running')?[running]:query.includes('status=queued')?[queued]:saved).map(summary),has_more:false,next_cursor:null});
  await mount();await paste('Keep unfinished work');
  assert.ok(button('New review').closest('#reports-panel'));
  assert.equal(document.querySelector('#studio-panel [aria-label="New review"]'),null);
  assert.deepEqual([...document.querySelectorAll('.report-group-label')].map(el=>el.textContent),['Recent']);
  const rows=[...document.querySelectorAll('.report-row')];
  assert.equal(rows.length,22);
  assert.match(rows[0].textContent!,/qr_running.*Reviewing/);
  assert.match(rows[1].textContent!,/qr_queued.*Queued/);
  assert.match(rows[2].textContent!,/qr_saved_19/);
  await act(async()=>{(rows[2] as HTMLButtonElement).click();});
  assert.equal(button('Current review').classList.contains('selected'),false);
  assert.equal(document.querySelectorAll('.scope-nav .selected').length,1);
  await click('New review');assert.equal(text(),'Keep unfinished work');
  assert.equal(button('Current review').classList.contains('selected'),true);
});


test('comment feedback shares one dialog, sends version and optional wording, and leaves copy text intact', async () => {
  const source = {...review('qr-comment-feedback','Findings: controlled. Impression: controlled.'), execution_status:'completed',
    result:{outcome:'observations',general_comments:[{observation_id:'obs-1',comment:'General comment.'}],
      critical_comments:[{observation_id:'obs-2',comment:'Critical comment.'}],comments_copy_text:'Original copy text.'}} as Review;
  const originalFeedback = api.feedback, originalHistory = api.feedbackHistory;
  const sent: any[] = [];
  let historyReads = 0;
  api.feedbackHistory = async () => {historyReads++; return {items:[],has_more:false,next_cursor:null};};
  api.feedback = async (_id, payload, key) => {sent.push({payload,key}); return {} as any;};
  function Output({disabled=false}: {disabled?:boolean}) {
    const [open,setOpen] = useState(false);
    return <ReviewOutput review={source} stale={disabled} disconnected={false} restore={()=>{}} feedbackOpen={open} setFeedbackOpen={setOpen}/>;
  }
  try {
    await act(async()=>root.render(<Output/>));
    assert.equal(historyReads,1);
    assert.equal(document.querySelectorAll('.comment-feedback').length,2);
    assert.equal(document.querySelectorAll('dialog').length,1);
    await click('Mark comment obs-1 useful');
    assert.deepEqual(sent[0].payload,{rating:'up',target:'observation',expected_input_version:1,observation_id:'obs-1'});
    await click('Suggest improvement for comment obs-2');
    assert.equal(document.querySelector('dialog blockquote')!.textContent,'Critical comment.');
    await act(async()=>document.querySelector('form.feedback-form')!.dispatchEvent(new window.Event('submit',{bubbles:true,cancelable:true})));
    assert.equal(sent.length,1);
    await act(async()=>{
      const reason = document.querySelector('#feedback-reason') as HTMLSelectElement;
      reason.value='unclear_wording'; reason.dispatchEvent(new window.Event('change',{bubbles:true}));
      const details = document.querySelector('#feedback-details') as HTMLTextAreaElement;
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value')!.set!.call(details,'Please clarify this comment.');
      details.dispatchEvent(new window.Event('input',{bubbles:true}));
    });
    await act(async()=>document.querySelector('form.feedback-form')!.dispatchEvent(new window.Event('submit',{bubbles:true,cancelable:true})));
    assert.deepEqual(sent[1].payload,{rating:'down',target:'observation',expected_input_version:1,observation_id:'obs-2',reason:'unclear_wording',explanation:'Please clarify this comment.'});
    assert.equal(document.querySelector('#feedback-wording'),null);
    assert.equal(source.result!.comments_copy_text,'Original copy text.');
    await click('Thumbs up');
    assert.equal(sent[2].payload.target,'result');
    assert.equal(sent[2].payload.observation_id,undefined);
    await act(async()=>root.render(<Output disabled/>));
    assert.ok(button('Mark comment obs-1 useful').disabled);
    assert.ok(button('Suggest improvement for comment obs-2').disabled);
  } finally {api.feedback=originalFeedback;api.feedbackHistory=originalHistory;}
});
