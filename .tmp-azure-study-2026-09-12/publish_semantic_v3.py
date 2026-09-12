from pathlib import Path
src=Path('.tmp-azure-study-2026-09-12/publish.py').read_text()
lines=[]
for line in src.splitlines():
    s=line.strip()
    indent=line[:len(line)-len(line.lstrip())]
    if 'architecture diagram placement' in line and s.startswith('if not re.search'):
        lines.append(indent+"if not re.search(r'<h3>Architecture[^<]*</h3>.*?src=\"images/[^\"]+\\.svg\"',sec,re.S|re.I): raise SystemExit(f'L{n} architecture diagram placement')")
    elif 'full-width diagram css missing' in line and s.startswith('if not re.search'):
        lines.append(indent+"if not re.search(r'(?:figure\\.)?diagram[^\\{]*img\\s*\\{[^}]*width\\s*:\\s*100%',data,re.I): raise SystemExit('full-width diagram css missing')")
    elif s.startswith("mm=re.search(r'<figure class=\"diagram\">"):
        lines.append(indent+"mm=re.search(r'src=\"images/([^\"]+\\.svg)\"',sec,re.S|re.I)")
    elif s == 'questions=json.loads(m.group(1))':
        lines.append(indent+'raw_questions=m.group(1)')
        lines.append(indent+'buf=[]; in_string=False; escaped=False')
        lines.append(indent+'for ch in raw_questions:')
        lines.append(indent+'    if in_string:')
        lines.append(indent+'        if escaped:')
        lines.append(indent+'            buf.append(ch); escaped=False')
        lines.append(indent+"        elif ch=='\\\\':")
        lines.append(indent+'            buf.append(ch); escaped=True')
        lines.append(indent+"        elif ch=='\"':")
        lines.append(indent+'            buf.append(ch); in_string=False')
        lines.append(indent+'        elif ord(ch)<32:')
        lines.append(indent+"            buf.append({'\\n':'\\\\n','\\r':'\\\\r','\\t':'\\\\t'}.get(ch,'\\\\u%04x'%ord(ch)))")
        lines.append(indent+'        else: buf.append(ch)')
        lines.append(indent+'    else:')
        lines.append(indent+'        buf.append(ch)')
        lines.append(indent+"        if ch=='\"': in_string=True")
        lines.append(indent+"sanitized_questions=''.join(buf)")
        lines.append(indent+'questions=json.loads(sanitized_questions)')
        lines.append(indent+"data=data[:m.start(1)]+json.dumps(questions,ensure_ascii=False,separators=(',',':'))+data[m.end(1):]")
        lines.append(indent+"out.write_text(data,encoding='utf-8')")
    else:
        lines.append(line)
exec(compile('\n'.join(lines),'publish_semantic_v3.py','exec'))
