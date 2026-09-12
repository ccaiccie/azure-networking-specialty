from pathlib import Path
import base64,re,json,collections
parts=sorted(Path('.tmp-azure-study-2026-09-12').glob('report.part*.b64'))
data=base64.b64decode(''.join(p.read_text().strip() for p in parts)).decode('utf-8')
m=re.search(r'const\s+questions\s*=\s*(\[.*?\]);',data,re.S)
raw=m.group(1)
buf=[]; inside=False; esc=False
for ch in raw:
    if inside:
        if esc: buf.append(ch); esc=False
        elif ch=='\\': buf.append(ch); esc=True
        elif ch=='"': buf.append(ch); inside=False
        elif ord(ch)<32: buf.append({'\n':'\\n','\r':'\\r','\t':'\\t'}.get(ch,'\\u%04x'%ord(ch)))
        else: buf.append(ch)
    else:
        buf.append(ch)
        if ch=='"': inside=True
q=json.loads(''.join(buf))
c=collections.Counter(x['domain'] for x in q)
print('total',len(q)); print('counts',dict(c))
for dom in c:
    print('\nDOMAIN',dom)
    for i,x in enumerate([z for z in q if z['domain']==dom],1): print(i,'L'+str(x['lesson']),x['text'])
