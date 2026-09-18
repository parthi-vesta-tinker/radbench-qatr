"""Offline artifact consistency checks; no clinical, model or interactive UI testing."""
import json
from pathlib import Path
r=Path(__file__).resolve().parent
for name in ['FRAMEWORK.md','DECISIONS.md','QA_COMMENTS.md','AGENT_HANDOFF.md','REVISION_REVIEW.md','BLUEPRINT.html','assets/reference-ui.png','comment-packets.json','README.md','GUIDED_ACTIONS.md','DESIGN_SYSTEM.md','UI_SYSTEM_DESIGN.md','guidance-examples.json','fleet-rows.json','design-tokens.json','design-tokens.css','assets/reference-expanded.png','assets/style-graphite.png','assets/style-warm-paper.png','assets/style-slate.png']:
 assert (r/name).is_file(), name
f=json.loads((r/'fixtures.json').read_text(encoding="utf-8")); p=json.loads((r/'comment-packets.json').read_text(encoding="utf-8"))
assert f['synthetic'] and p['synthetic']
assert f['framework_version']==p['framework_version']=='1.2'
cases={c['id']:c for c in f['cases']};assert len(cases)==3
for c in cases.values():
 sources={s['id']:s for s in c['sources']};evidence={e['id']:e for e in c['evidence']}; findings={x['id']:x for x in c['findings']}
 for src in sources.values():
  if src['kind']=='report':
   assert src['authors'] and src['signature']['status'] in ['signed','unsigned','unknown']
   assert src['document_status'] in ['draft','preliminary','final','amended','unknown']
 for e in evidence.values():
  src=sources[e['source_id']];assert src['version']==e['source_version']; assert e['quote'] in src['sections'][e['section']]
 for x in findings.values():
  assert x['type'] in ['suggestion','discrepancy','unmet_requirement']; assert set(x['evidence_ids'])<=evidence.keys()
  assert x['urgency'] in ['critical_review','non_critical','unclassified'];assert 'confirmation_status' in x
  if x['type']=='unmet_requirement':assert x['requirement_id']
 for check in c['checks']:
  assert set(check['source_ids'])<=sources.keys();assert set(check['finding_ids'])<=findings.keys()
 if c['coverage']=='complete':assert all(x['execution']=='completed' for x in c['checks'])
 for up in c['upstream_qa']['records']:
  assert sources[up['source_id']]['version']==up['source_version'];assert up['scope'] and up['producer']
  assert up['trust_status']=='received_unverified' and up['local_coverage_credit'] is False
 assert all(e['case_id']==c['id'] for e in c['events'])
 assert c['handoff']['report_source_id'] in sources
 if c['handoff']['status']=='acknowledged':assert c['handoff']['receipt']['report_source_id']==c['handoff']['report_source_id']
assert cases['R-201']['handoff']['status']=='acknowledged' and not cases['R-201']['findings']
assert cases['R-207']['communications'][-1]['interpretation']=='unclear'
assert cases['R-207']['decisions'][0]['status']=='awaiting_clarification'
assert cases['R-207']['handoff']['status']=='held'
assert cases['R-209']['findings'][0]['confirmation_status']=='confirmation_needed'
profiles={(x['id'],x['version']):x for x in p['profiles']};export_count=0
for packet in p['packets']:
 c=cases[packet['case_id']];src=next(x for x in c['sources'] if x['id']==packet['source_id']);findings={x['id']:x for x in c['findings']}
 assert packet['source_version']==src['version'] and packet['signature_status']==src['signature']['status']
 assert packet['review_run_id']==c['review_run_id']; assert packet['recipient']['role']=='radiologist'
 profile=profiles[(packet['profile_id'],packet['profile_version'])];assert profile['provenance'] and not profile['permissions_granted']
 assert packet['content_status']=='draft' and packet['transfer_status']=='not_copied' and packet['delivery_status']=='unknown'
 assert packet['correction_status']=='not_performed'
 assert set(packet['prior_exchange_ids'])<={m['id'] for m in c['communications']}
 seen=set();expected=[]
 assert [s['id'] for s in packet['sections']]==['critical','non_critical']
 for s in packet['sections']:
  for x in s['items']:
   issue=findings[x['finding_id']];seen.add(issue['id']); assert x['type']==issue['type']
   assert set(x['evidence_ids'])==set(issue['evidence_ids'])
   assert issue['urgency']==('critical_review' if s['id']=='critical' else 'non_critical')
  if not s['items']:assert s['id'] not in packet['exports'];continue
  title='CRITICAL-REVIEW COMMENTS — CONFIRMATION NEEDED' if s['id']=='critical' else 'NON-CRITICAL QA COMMENTS'
  if s['id']=='non_critical' and all(findings[x['finding_id']]['optional'] for x in s['items']):title+=' — OPTIONAL SUGGESTION'
  text=f"QA review | {packet['case_locator']} | Report v{src['version']} ({src['signature']['status']})\n{title}\n"+'\n'.join(str(i+1)+'. '+x['text'] for i,x in enumerate(s['items']))+'\n'
  assert packet['exports'][s['id']]['text']==text;expected.append(text)
 assert {x['id'] for x in findings.values() if not x['optional']}<=seen
 assert packet['exports']['all']['text']=='\n'.join(expected)
 for export in packet['exports'].values():
  assert (r/export['path']).read_text(encoding="utf-8")==export['text']; assert '{' not in export['text']
  assert 'no critical findings' not in export['text'].lower();export_count+=1
assert len(p['packets'])==3 and export_count==7
assert f['workspace']['selected_packet_id'] in {x['id'] for x in p['packets']}
print('PASS: 3 synthetic cases; exact evidence/source versions; authorship/signature and upstream scope; 3 typed, profile-bound comment packets; 7 matching plain-text exports; independent communication states.')

assert f['workspace']['review_mode']=='compact' and 'qa_subview' not in f['workspace']
g=json.loads((r/'guidance-examples.json').read_text(encoding="utf-8")); rows=json.loads((r/'fleet-rows.json').read_text(encoding="utf-8"))
packets={x['id']:x for x in p['packets']}
assert g['synthetic'] and g['framework_version']==f['framework_version']
assert len(g['guidance'])==3
for step in g['guidance']:
 c=cases[step['case_id']];src=next(x for x in c['sources'] if x['id']==step['source_id'])
 assert step['source_version']==src['version'] and step['actor'] and step['completion_evidence'] and step['provenance']
 assert step['destination']['mapping_status']=='configured_demo'
 if step['packet_id']:
  pkt=packets[step['packet_id']]
  assert pkt['case_id']==c['id'] and pkt['revision']==step['packet_revision']
  assert pkt['recipient']['id']==step['recipient'] and step['comment_section'] in pkt['exports']
assert len(rows['rows'])==8 and len({x['case_id'] for x in rows['rows']})==8
for row in rows['rows']:
 if row['canonical_case']:
  case=cases[row['case_id']]
  assert all(row[k]==case[k] for k in ['exam','coverage','qa_outcome'])
 else:assert row['case_id'] not in cases
# Check semantic color pairs, not generated-image pixels or full component accessibility.
tokens=json.loads((r/'design-tokens.json').read_text(encoding="utf-8"));css=(r/'design-tokens.css').read_text(encoding="utf-8")
def lum(h):
 rgb=[int(h[i:i+2],16)/255 for i in [1,3,5]]
 rgb=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in rgb]
 return sum(x*w for x,w in zip(rgb,[.2126,.7152,.0722]))
def contrast(a,b):
 a,b=sorted([lum(a),lum(b)]);return (b+.05)/(a+.05)
for theme,colors in tokens['themes'].items():
 for name in ['text','text-muted','accent','attention','urgent']:
  assert contrast(colors[name],colors['surface'])>=4.5,(theme,name)
 assert contrast(colors['text'],colors['selection'])>=4.5
 assert contrast(colors['focus'],colors['surface'])>=3
 assert contrast(colors['control-border'],colors['surface'])>=3
 for key,value in colors.items():assert '--qa-'+key+': '+value+';' in css
print('PASS: compact default; 3 bound guidance records; 8 fleet rows; 3 theme text/focus/control contrast checks and matching CSS tokens. No rendered-app or performance validation.')

assert {str(x.relative_to(r)) for x in (r/"comment-examples").glob("*.txt")} == {x["path"] for pkt in p["packets"] for x in pkt["exports"].values()}
