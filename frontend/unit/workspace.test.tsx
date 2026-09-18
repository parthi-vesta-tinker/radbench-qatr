// DOM/state tests use API doubles. They do not exercise or simulate clinical AI quality.
import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { Window } from 'happy-dom';
import { act } from 'react';
import App from '../src/App';
import { api, ApiError } from '../src/api';
import type { Review } from '../src/types';
import { OutcomeLog } from '../src/OutcomeLog';
import type { Analytics, OutcomeRecord, KnowledgeCatalog, KnowledgeDetail, KnowledgeDraftInput } from '../src/types';
const window = new Window({url:'http://localhost:8000'});
Object.assign(globalThis, {window, document:window.document, HTMLElement:window.HTMLElement,
  sessionStorage:window.sessionStorage, localStorage:window.localStorage, IS_REACT_ACT_ENVIRONMENT:true});
const {createRoot} = await import('react-dom/client');
let root: ReturnType<typeof createRoot>;
let requests: {text:string; key:string}[];
const results = new Map<string, Review>();
function review(id:string,text:string): Review { return {id,object:'qa_review', tenant_id:'vesta',api_version:'2026-09-18',input:{report_text:text},execution_status:'running',steps:[],result:null,error:null,provenance:{mode:'openai',policy_status:'provisional_no_manual'}}; }
function button(name: string) { const node=[...document.querySelectorAll('button')].find(el=>el.getAttribute('aria-label')===name || el.textContent?.trim()===name); assert.ok(node, `Missing button: ${name}`); return node as HTMLButtonElement; }
async function click(name:string) { await act(async()=>{button(name).click();}); }
async function paste(text:string) { await act(async()=>{const input=document.querySelector('#report-text') as HTMLTextAreaElement; assert.ok(input && !input.readOnly); Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value')!.set!.call(input,text);input.dispatchEvent(new window.Event('input',{bubbles:true}));}); }
async function mount() {await act(async()=>{root.render(<App/>);});}
const text = () => (document.querySelector('#report-text') as HTMLTextAreaElement).value;
const analytics = (): Analytics => ({object:'qa_analytics',tenant_id:'vesta',checked_at:new Date().toISOString(),period:'7d',period_start:null,source:'openai',reviews:{total:0,with_comments:0,no_comments:0,critical:0,statuses:{queued:0,running:0,completed:0,needs_input:0,failed:0}},feedback:{total:0,reviews:0,up:0,down:0,reasons:{}},acceptance:[],critical_evaluation:{status:'not_measured',precision:null,recall:null,false_positive_rate:null,false_alert_share:null,reason:'No adjudicated reference cohort.'}});
const knowledgeDetail = (): KnowledgeDetail => ({document:{document_id:'skill_test',title:'Review instructions',kind:'skill',description:'Controlled editorial content.',source_path:'skills/test/SKILL.md',version:'0.2.0',source_sha256:'a'.repeat(64),stages:['critical_finding_review'],used_by:['test'],runtime_use:'model_instruction',latest_revision:0,has_changes:false,source_changed:false},package_sha256:'b'.repeat(64),installed_content:'Installed instructions.',draft:null,saved_diff:'',recent_revisions:[],history_truncated:false});
const knowledgeCatalog = (): KnowledgeCatalog => ({package_version:'0.2.0',package_sha256:'b'.repeat(64),can_edit:true,items:[knowledgeDetail().document]});
async function field(id:string,value:string) {await act(async()=>{const input=document.getElementById(id)!;const prototype=input.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(prototype,'value')!.set!.call(input,value);input.dispatchEvent(new window.Event('input',{bubbles:true}));});}
async function choose(label:string,value:string) { await act(async()=>{const select=[...document.querySelectorAll('label')].find(n=>n.textContent?.startsWith(label))?.querySelector('select');assert.ok(select);select.value=value;select.dispatchEvent(new window.Event('change',{bubbles:true}));}); }
beforeEach(()=>{
  sessionStorage.clear();localStorage.clear();results.clear();requests=[];
  document.body.innerHTML='<div id="root"></div>';root=createRoot(document.getElementById('root')!);
  api.config=async()=>({tenant_id:'vesta',api_version:'2026-09-18',mode:'openai',ready:true,model:'configured-model',policy_status:'provisional_no_manual',samples:[]});
  api.status=async()=>({status:'ready',checked_at:new Date().toISOString(),readiness_scope:'Local checks only',components:{api:{status:'ok',message:'API responds'},dbos:{status:'ok',message:'Checkpoint store responds'},openai:{status:'configured',message:'Inference not verified'}}});
  api.history=async()=>({items:[],has_more:false,next_cursor:null});
  api.feedbackInbox=async()=>({items:[],has_more:false,next_cursor:null});
  api.analytics=async()=>analytics();
  api.outcomes=async()=>({items:[],has_more:false,next_cursor:null});
  api.knowledgeCatalog=async()=>knowledgeCatalog();
  api.knowledgeDetail=async()=>knowledgeDetail();
  window.confirm=()=>false;
  api.get=async(id)=>{const r=results.get(id);assert.ok(r);return r;};
  api.create=async(input,key)=>{requests.push({text:input.report_text,key});const r=review('qr-'+requests.length,input.report_text);results.set(r.id,r);return r;};
});
afterEach(async()=>{await act(async()=>root.unmount());});
test('draft deletion has Undo and does not remove another draft',async()=>{
  await mount();await paste('first draft');await click('New report');await paste('second draft');
  await click('Delete draft 1');assert.equal(text(),'second draft');assert.match(document.body.textContent!,/Draft deleted/);
  await click('Undo');assert.equal(text(),'first draft');assert.equal(document.querySelectorAll('.draft-row').length,2);
});
test('empty New report reuses a draft; deleting the final draft leaves usable input',async()=>{
  await mount();await click('New report');await click('New report');assert.equal(document.querySelectorAll('.draft-row').length,1);
  await click('Delete draft 1');assert.equal(text(),'');assert.equal(document.querySelectorAll('.draft-row').length,1);
});
test('submitted input is locked and new work can proceed',async()=>{
  await mount();await paste('Findings: source A. Impression: source A.');await click('Review report');
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,true);
  await click('New report');await paste('Findings: source B. Impression: source B.');await click('Review report');
  assert.equal(requests.length,2);assert.notEqual(requests[0].key,requests[1].key);
});
test('late acceptance never replaces a newly selected draft',async()=>{
  let accept!:(r:Review)=>void;
  api.create=()=>new Promise(resolve=>{accept=resolve;});
  await mount();await paste('first input');await click('Review report');
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,true);
  await click('New report');await paste('second input');
  const r=review('qr-late','first input');results.set(r.id,r);
  await act(async()=>accept(r));assert.equal(text(),'second input');assert.equal(document.querySelectorAll('.draft-row').length,1);
});
test('ambiguous network failure locks input and retries the identical operation',async()=>{
  let calls=0;
  api.create=async(input,key)=>{requests.push({text:input.report_text,key});if(calls++===0)throw new ApiError(0,'QA_CONNECTION_FAILED','Connection lost');const r=review('qr-retry',input.report_text);results.set(r.id,r);return r;};
  await mount();await paste('immutable request');await click('Review report');
  assert.equal((document.querySelector('#report-text') as HTMLTextAreaElement).readOnly,true);
  assert.equal(button('Delete draft 1').disabled,true);
  await click('Retry submission');assert.equal(requests.length,2);assert.deepEqual(requests[0],requests[1]);
});
test('theme persists and environment controls and canned input controls are absent',async()=>{
  await mount();await click('Switch to dark theme');assert.equal(document.documentElement.dataset.theme,'dark');assert.equal(localStorage.getItem('vesta.theme'),'dark');
  await click('Switch to light theme');assert.equal(document.documentElement.dataset.theme,'light');
  assert.equal(document.querySelector('[aria-label="Execution mode for new reviews"]'),null);assert.equal(document.querySelector('[aria-label="Load synthetic example"]'),null);
});
test('health reports unavailable truthfully and double-click opens details',async()=>{
  api.status=async()=>{throw new ApiError(0,'QA_CONNECTION_FAILED','Service unavailable');};
  await mount();const summary=document.querySelector('.system-status summary')!;assert.match(summary.textContent!,/Unavailable/);
  await act(async()=>summary.dispatchEvent(new window.MouseEvent('dblclick',{bubbles:true})));
  assert.equal((document.querySelector('.system-status') as HTMLDetailsElement).open,true);
});
test('Studio navigation preserves report input and exposes distinct tools',async()=>{
  await mount();await paste('draft to preserve');await click('Review history');await click('Current report');assert.equal(text(),'draft to preserve');
  await click('Feedbacks');assert.match(document.querySelector('.history-pane h1')!.textContent!,/Feedbacks/);
  await click('Analytics');assert.match(document.querySelector('.history-pane')!.textContent!,/Not measured/);
  await click('Current report');assert.equal(text(),'draft to preserve');
});

test('feedback inbox reads notes and opens associated report without losing draft',async()=>{
  const r=review('qr-feedback','Associated report');results.set(r.id,r);
  api.feedbackInbox=async query=>{assert.equal(new URLSearchParams(query).get('rating'),'down');return {items:[{feedback:{id:'qf-1',review_id:r.id,created_at:new Date().toISOString(),result_version:1,rating:'down',target:'result',reason:'unclear_wording',explanation:'Make the comment shorter.'},report_preview:'Associated report',source:'openai',target_comment:null}],has_more:false,next_cursor:null};};
  await mount();await paste('preserved draft');await click('Feedbacks');
  assert.match(document.querySelector('.inbox-list')!.textContent!,/Make the comment shorter/);
  await click('Open report');assert.equal(text(),'Associated report');await click('Draft 1Draft');assert.equal(text(),'preserved draft');
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
  api.analytics=async()=>({...analytics(),reviews:{...analytics().reviews,total:237},acceptance:[{stakeholder:'qa',subject:'report',eligible:10,recorded:0,accepted:0,rejected:0,review_requested:0,unknown:0,not_recorded:10,acceptance_rate:null}]});
  await mount();await click('Analytics');const pane=document.querySelector('.operational-analytics')!;
  assert.match(pane.textContent!,/237/);assert.match(pane.textContent!,/0 \/ 0 final decisions/);
  assert.equal(pane.querySelectorAll('.measurement-grid strong').length,4);
  assert.ok([...pane.querySelectorAll('.measurement-grid strong')].every(el=>el.textContent==='Not measured'));
  await choose('Assess acceptance of','qa_comments');assert.equal(pane.querySelectorAll('tbody tr').length,0);
});

test('late analytics response cannot replace a new period',async()=>{
  let release!:(value:Analytics)=>void;
  api.analytics=query=>new URLSearchParams(query).get('period')==='7d' ? new Promise(resolve=>{release=resolve;}) : Promise.resolve({...analytics(),period:'30d',reviews:{...analytics().reviews,total:300}});
  await mount();await click('Analytics');await choose('Period','30d');
  await act(async()=>release({...analytics(),reviews:{...analytics().reviews,total:999}}));
  const totals=document.querySelector('[aria-label="Review totals"]')!.textContent!;assert.match(totals,/300/);assert.doesNotMatch(totals,/999/);
});

test('outcome form retries the same operation after lost confirmation',async()=>{
  const calls:{key:string;payload:unknown}[]=[];let first=true;
  api.saveOutcome=async(id,payload,key)=>{calls.push({key,payload});if(first){first=false;throw new ApiError(0,'QA_CONNECTION_FAILED','Lost confirmation');}return {...payload,outcome_id:'qo-test',review_id:id,created_at:new Date().toISOString(),recording_method:'operator_recorded'} as OutcomeRecord;};
  await act(async()=>root.render(<OutcomeLog reviewId="qr-outcome" resultVersion={1} disabled={false}/>));
  await act(async()=>{const details=document.querySelector('details')!;details.open=true;details.dispatchEvent(new window.Event('toggle'));});
  await act(async()=>{const input=document.querySelector('#outcome-source')!;Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value')!.set!.call(input,'QA reviewer requested clarification.');input.dispatchEvent(new window.Event('input',{bubbles:true}));});
  await click('Record outcome');assert.equal(document.querySelector('fieldset')!.disabled,true);
  await click('Retry same outcome');assert.equal(calls.length,2);assert.deepEqual(calls[0],calls[1]);
  assert.match(document.querySelector('.outcome-log')!.textContent!,/Outcome recorded/);
});

test('malformed success is an ambiguous outcome, not permission to create another',async()=>{
  api.saveOutcome=async()=>{throw new ApiError(201,'INVALID_API_RESPONSE','Response could not be read');};
  await act(async()=>root.render(<OutcomeLog reviewId="qr-outcome" resultVersion={1} disabled={false}/>));
  await act(async()=>{const details=document.querySelector('details')!;details.open=true;details.dispatchEvent(new window.Event('toggle'));});
  await act(async()=>{const input=document.querySelector('#outcome-source')!;Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value')!.set!.call(input,'A recorded decision.');input.dispatchEvent(new window.Event('input',{bubbles:true}));});
  await click('Record outcome');
  assert.equal(document.querySelector('fieldset')!.disabled,true);
  assert.equal(button('Retry same outcome').disabled,false);
});

test('Studio skills editor preserves unsaved edits across report navigation',async()=>{
  await mount();await paste('Report draft stays intact');await click('Skills & knowledge');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Installed instructions.');
  await field('knowledge-content','Proposed instructions.');
  await click('Compare with installed');
  assert.equal(document.querySelectorAll('.knowledge-content textarea').length,2);
  await click('Current report');assert.equal(text(),'Report draft stays intact');
  await click('Skills & knowledge');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Proposed instructions.');
  await click('Reload source');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Proposed instructions.'); // declined discard
});

test('draft save retry is idempotent and never changes installed content',async()=>{
  const calls:{payload:KnowledgeDraftInput;key:string}[]=[];
  api.saveKnowledgeDraft=async(id,payload,key)=>{calls.push({payload,key});if(calls.length===1)throw new ApiError(0,'LOST','Confirmation lost');return {...payload,draft_id:'kd-1',document_id:id,revision:1,content_sha256:'c'.repeat(64),created_at:new Date().toISOString(),status:'draft_not_active'};};
  await mount();await click('Skills & knowledge');await field('knowledge-content','Proposed instruction');await field('knowledge-note','Clarify behavior');
  await click('Save draft');assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,true);
  await click('Retry same save');assert.deepEqual(calls[0],calls[1]);
  assert.match(document.querySelector('.knowledge-pane')!.textContent!,/Draft revision 1 saved/);
  await click('Compare with installed');
  assert.equal((document.querySelector('.knowledge-content textarea[readonly]') as HTMLTextAreaElement).value,'Installed instructions.');
});

test('editor permissions and unavailable catalog are explicit',async()=>{
  let fail=true;api.knowledgeCatalog=async()=>{if(fail)throw new ApiError(503,'SOURCE_UNAVAILABLE','Source unavailable');return {...knowledgeCatalog(),can_edit:false};};
  await mount();await click('Skills & knowledge');assert.match(document.querySelector('.knowledge-pane [role="alert"]')!.textContent!,/Source unavailable/);
  fail=false;await click('Retry catalog');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,true);
  assert.equal(document.querySelector('#knowledge-note'),null);
});

test('revision conflict retains text for reconciliation',async()=>{
  api.saveKnowledgeDraft=async()=>{throw new ApiError(409,'KNOWLEDGE_REVISION_CONFLICT','A newer draft exists.');};
  await mount();await click('Skills & knowledge');await field('knowledge-content','Keep this proposal.');await field('knowledge-note','Reason');await click('Save draft');
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).value,'Keep this proposal.');
  assert.match(document.querySelector('.knowledge-pane [role="alert"]')!.textContent!,/A newer draft exists/);
  assert.equal((document.getElementById('knowledge-content') as HTMLTextAreaElement).readOnly,false);
});
