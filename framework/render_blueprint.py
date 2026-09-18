"""Rebuild the standalone reading edition; Python 3 stdlib only."""
from pathlib import Path
import re,html,base64
r=Path(__file__).resolve().parent
# A small renderer for the controlled Markdown used in these documents.
def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
    return s
def render(text,prefix):
    lines=text.splitlines(); out=[]; i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip(): i+=1; continue
        if line.startswith('```'):
            block=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):
                block.append(lines[i]);i+=1
            i+=1;out.append('<pre><code>'+html.escape('\n'.join(block))+'</code></pre>');continue
        if line.startswith('!['):
            m=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
            source=(r/m[2]).resolve();assert source.is_relative_to(r.resolve())
            image_uri='data:image/png;base64,'+base64.b64encode(source.read_bytes()).decode()
            out.append('<figure><img loading="lazy" alt="'+html.escape(m[1])+'" src="'+image_uri+'"><figcaption>'+html.escape(m[1])+'. Text contracts govern exact behavior.</figcaption></figure>');i+=1;continue
        if line.startswith('#'):
            m=re.match(r'(#+) (.*)',line);level=min(len(m[1])+1,6)
            slug=prefix+'-'+re.sub('[^a-z0-9]+','-',m[2].lower()).strip('-')
            out.append(f'<h{level} id="{slug}">{inline(m[2])}</h{level}>');i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=lines[i].strip().strip('|').split('|')
                if not all(re.fullmatch(r'\s*:?-+:?\s*',c) for c in cells): rows.append(cells)
                i+=1
            out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(c.strip())+'</th>' for c in rows[0])+'</tr></thead><tbody>')
            for row in rows[1:]: out.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in row)+'</tr>')
            out.append('</tbody></table></div>');continue
        if re.match(r'^(- |\d+\. )',line):
            ordered=bool(re.match(r'^\d+\.',line)); tag='ol' if ordered else 'ul';out.append('<'+tag+'>')
            while i<len(lines) and re.match(r'^(- |\d+\. )',lines[i]):
                out.append('<li>'+inline(re.sub(r'^(- |\d+\. )','',lines[i]))+'</li>');i+=1
            out.append('</'+tag+'>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|```|\||!\[|- |\d+\. )',lines[i]):para.append(lines[i]);i+=1
        out.append('<p>'+inline(' '.join(para))+'</p>')
    return '\n'.join(out)
css='''body{margin:0;background:#f5f6f8;color:#20242b;font:16px/1.65 system-ui,-apple-system,sans-serif}header{background:#20242b;color:white;padding:52px max(5vw,24px)}header small{color:#d5d7dc;letter-spacing:.12em}header h1{font-size:42px;line-height:1.15;max-width:900px}header p{max-width:820px;color:#d5d7e8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f6f8;padding:16px;border-left:3px solid #737d8c}pre code{padding:0}nav{flex-wrap:wrap;position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;display:flex;gap:24px;padding:16px max(5vw,24px);z-index:2}a{color:#245bb2}main{max-width:1100px;margin:auto;background:white;padding:36px 52px}h2{font-size:30px;margin-top:48px;border-top:3px solid #737d8c;padding-top:24px}h3{font-size:23px;margin-top:36px}h4{font-size:19px}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.5;margin:16px 0}th{text-align:left;background:#f0f2f5;color:#24203e}td,th{padding:11px 13px;border-bottom:1px solid #dedee9;vertical-align:top}tr:nth-child(even){background:#fafafe}.table-wrap{overflow-x:auto}code{background:#f0f2f5;padding:2px 5px;font-size:.9em}figure{margin:24px -20px}img{width:100%;height:auto;border:1px solid #ddd}figcaption{font-size:13px;color:#666}section{scroll-margin-top:70px}footer{padding:32px;color:#666;text-align:center}@media(max-width:700px){main{padding:20px}header h1{font-size:32px}nav{gap:14px;font-size:13px}figure{margin:20px 0}}@media print{nav{position:static}main{padding:0}body{background:white}header{padding:20px;color:#20242b;background:white}header p,header small{color:#333}table{font-size:10px}tr{break-inside:avoid}h2,h3,h4{break-after:avoid}}'''
sections=[]
for name,key in [('FRAMEWORK.md','framework'),('DESIGN_SYSTEM.md','design-system'),('UI_SYSTEM_DESIGN.md','architecture'),('QA_COMMENTS.md','comments'),('GUIDED_ACTIONS.md','guidance'),('DECISIONS.md','decisions'),('AGENT_HANDOFF.md','handoff'),('REVISION_REVIEW.md','revision'),('PACKAGE_CHECKS.md','checks')]:
    sections.append('<section id="'+key+'">'+render((r/name).read_text(),key)+'</section>')
examples=[]
for path in sorted((r/'comment-examples').glob('*.txt')):
    examples.append('<h3>'+html.escape(path.name)+'</h3><pre><code>'+html.escape(path.read_text())+'</code></pre>')
sections.append('<section id="examples"><h2>Exact plain-text comment examples</h2><p>Synthetic draft outputs. Select text to copy; this reading edition does not send or record delivery.</p>'+''.join(examples)+'</section>')
nav=''.join('<a href="#'+key+'">'+label+'</a>' for key,label in [('framework','Framework'),('design-system','Styles & components'),('architecture','UI architecture'),('comments','QA comments'),('guidance','Next steps'),('examples','Text examples'),('decisions','Decisions'),('handoff','Agent handoff'),('revision','Revision review'),('checks','Checks')])
doc='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Vesta report QA — UX framework v1.2</title><style>'+css+'</style><header><small>VESTA · FRAMEWORK BLUEPRINT · V1.2</small><h1>A familiar workspace for increasingly autonomous report QA</h1><p>Compact comments and contextual next steps, one-click expanded review, the selected fleet-first layout and compact vertical Studio, and a lightweight UI system design. For human designers and coding agents.</p></header><nav>'+nav+'</nav><main>'+''.join(sections)+'</main><footer>13 September 2026 · Design baseline · No production or clinical validation claimed</footer></html>'
(r/'BLUEPRINT.html').write_text(doc)
print('Rebuilt standalone BLUEPRINT.html from canonical sources and exact comment exports.')
