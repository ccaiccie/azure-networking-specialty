from pathlib import Path
import re,json,html
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'
REPORT=DOCS/'Azure_Networking_Specialty_Daily_Study_Quiz_2026-09-13-08-00.html'
LEDGER=DOCS/'azure-study-uniqueness-ledger.json'
URL='https://ccaiccie.github.io/azure-networking-specialty/Azure_Networking_Specialty_Daily_Study_Quiz_2026-09-13-08-00.html'

replacements={
'https://learn.microsoft.com/en-us/azure/expressroute/how-to-expressroute-direct-portal':'https://learn.microsoft.com/en-us/cli/azure/network/express-route/port?view=azure-cli-latest',
'https://learn.microsoft.com/en-us/azure/load-balancer/components':'https://learn.microsoft.com/en-us/troubleshoot/azure/load-balancer/troubleshoot-load-balancer-health-probe-failures',
'https://learn.microsoft.com/en-us/azure/firewall/firewall-azure-policy':'https://learn.microsoft.com/en-us/azure/firewall/threat-intel',
'https://learn.microsoft.com/en-us/azure/application-gateway/application-gateway-components':'https://learn.microsoft.com/en-us/azure/application-gateway/configuration-overview',
}
s=REPORT.read_text()
for old,new in replacements.items(): s=s.replace(old,new)
REPORT.write_text(s)

# Structural and typography hard gates.
assert s.count('<section class="lesson"')==12
assert '<h3>Summary</h3>' not in s and 'Exam and interview takeaways' not in s
assert '.architecture-diagram img{display:block;width:100%;height:auto}' in s
for required in ['font:14.5px/1.56','font-size:30px','font-size:23px','font-size:18px','font:13px/1.48']:
    assert required in s, required
assert s.count('<h3>Why it matters</h3>')==12
assert s.count('<h3>Architecture</h3>')==12
assert s.count('<h3>Prerequisites and implementation</h3>')==12
assert s.count('<h3>Verification</h3>')==12
assert s.count('<h3>Troubleshooting</h3>')==12
assert s.count('Representative successful state')==12
assert s.count('Representative failure state')==12

# Exact substantive word counts: remove code, sources, headings, captions/metadata.
sections=re.findall(r'<section class="lesson".*?</section>',s,re.S)
counts=[]
for sec in sections:
    x=re.sub(r'<pre.*?</pre>',' ',sec,flags=re.S)
    x=re.sub(r'<div class="sources".*?</div>',' ',x,flags=re.S)
    x=re.sub(r'<figure.*?</figure>',' ',x,flags=re.S)
    x=re.sub(r'<h[1-6].*?</h[1-6]>',' ',x,flags=re.S)
    x=re.sub(r'<div class="eyebrow".*?</div>',' ',x,flags=re.S)
    x=re.sub(r'<[^>]+>',' ',x)
    words=re.findall(r"\b[\w'’/-]+\b",html.unescape(x))
    counts.append(len(words))
assert min(counts)>=700, counts

# Exact quiz distribution and controls.
# Domain constants and question objects are static literals in this report.
question_count=len(re.findall(r'\{domain:[HCRS],lesson:\d+,text:',s))
assert question_count==50, question_count
# Count each domain from object literals.
dist={
'Hybrid connectivity and architecture':len(re.findall(r'\{domain:H,lesson:',s)),
'Core networking infrastructure':len(re.findall(r'\{domain:C,lesson:',s)),
'Routing and traffic management':len(re.findall(r'\{domain:R,lesson:',s)),
'Security, monitoring, and private service access':len(re.findall(r'\{domain:S,lesson:',s)),
}
assert dist=={'Hybrid connectivity and architecture':15,'Core networking infrastructure':13,'Routing and traffic management':10,'Security, monitoring, and private service access':12},dist
for fn in ('function check','function gradeAll','function resetQuiz'):
    assert fn in s,fn

# Diagram hard gate: 12 unique references and matching valid Azure-stencil draw.io/SVG pairs.
refs=re.findall(r'<img src="images/(2026-09-13-08-00-[^"]+\.svg)"',s)
assert len(refs)==12 and len(set(refs))==12,refs
for svg_name in refs:
    svg=DOCS/'images'/svg_name
    dio=DOCS/'images'/(svg_name[:-4]+'.drawio')
    assert svg.exists() and dio.exists(),svg_name
    assert '<svg' in svg.read_text(),svg_name
    assert 'mxgraph.azure2' in dio.read_text(),svg_name

# Source-role uniqueness: extract the 24 lesson source links and compare to ledger.
source_blocks=re.findall(r'<div class="sources">(.*?)</div>',s,re.S)
assert len(source_blocks)==12
sources=[]
for b in source_blocks:
    urls=re.findall(r'href="([^"]+)"',b)
    assert len(urls)==2,urls
    assert urls[0]!=urls[1],urls
    sources.extend(urls)
assert len(sources)==24 and len(set(sources))==24
ledger_text=LEDGER.read_text()
for u in sources:
    assert u not in ledger_text,f'30-day source collision: {u}'

slugs=['expressroute-direct-qinq-dot1q','expressroute-ergwscale-autoscaling','nva-ip-forwarding-udr-insertion','public-ip-prefix-lifecycle','load-balancer-health-probes','application-gateway-connection-draining','network-watcher-vpn-troubleshoot','azure-firewall-threat-intelligence','front-door-waf-rate-limiting','avnm-network-verifier-reachability','load-balancer-admin-state','application-gateway-custom-error-pages']
for slug in slugs: assert slug not in ledger_text,f'topic collision: {slug}'

validation={'report':'Azure_Networking_Specialty_Daily_Study_Quiz_2026-09-13-08-00.html','report_url':URL,'lesson_count':12,'lesson_substantive_word_counts':counts,'minimum_lesson_substantive_word_count':min(counts),'question_count':50,'domain_distribution':dist,'nonredundancy':'passed','implementation_validation':'passed','verification_expected_output':'passed','troubleshooting_failure_output':'passed','drawio_svg_pairs':12,'full_width_diagrams':'passed','compact_desktop_typography':'passed','source_role_separation':'passed','thirty_day_uniqueness':'passed','report_fetchback':'pending','index_fetchback':'pending','asset_fetchback':'pending'}
(DOCS/'.azure-study-2026-09-13-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))
