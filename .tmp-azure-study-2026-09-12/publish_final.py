from pathlib import Path
src=Path('.tmp-azure-study-2026-09-12/publish.py').read_text()
lines=[]
for line in src.splitlines():
    s=line.strip()
    indent=line[:len(line)-len(line.lstrip())]
    if s.startswith("data=base64.b64decode(payload).decode"):
        lines.append(line)
        lines.append(indent+"data=data.replace('https://learn.microsoft.com/en-us/azure/traffic-manager/traffic-manager-routing-methods','https://learn.microsoft.com/en-us/azure/traffic-manager/tutorial-traffic-manager-subnet-routing')")
        lines.append(indent+"data=data.replace('https://learn.microsoft.com/en-us/azure/firewall/premium-features','https://learn.microsoft.com/en-us/azure/firewall/web-categories')")
    elif 'architecture diagram placement' in line and s.startswith('if not re.search'):
        lines.append(indent+"if not re.search(r'<h3>Architecture[^<]*</h3>.*?src=\"images/[^\"]+\\.svg\"',sec,re.S|re.I): raise SystemExit(f'L{n} architecture diagram placement')")
    elif 'full-width diagram css missing' in line and s.startswith('if not re.search'):
        lines.append(indent+"if not re.search(r'(?:figure\\.)?diagram[^\\{]*img\\s*\\{[^}]*width\\s*:\\s*100%',data,re.I): raise SystemExit('full-width diagram css missing')")
    elif s.startswith("mm=re.search(r'<figure class=\"diagram\">"):
        lines.append(indent+"mm=re.search(r'src=\"images/([^\"]+\\.svg)\"',sec,re.S|re.I)")
    elif s.startswith("for token in ('Check answer','Finish and grade','Reset quiz'"):
        lines.append(indent+"for token in ('Check answer','Finish and grade','function finishQuiz','function resetQuiz'):")
    elif s.startswith("if token not in data: raise SystemExit(f'quiz control missing"):
        lines.append(line)
        lines.append(indent+"if not re.search(r'<button[^>]*(?:onclick=\"resetQuiz\\(\\)\"|id=\"reset[^\"]*\")[^>]*>\\s*Reset(?: quiz)?\\s*</button>',data,re.I): raise SystemExit('visible reset control missing')")
    elif s == 'questions=json.loads(m.group(1))':
        lines.append(indent+'raw_questions=m.group(1)')
        lines.append(indent+'buf=[]; in_string=False; escaped=False')
        lines.append(indent+'for ch in raw_questions:')
        lines.append(indent+'    if in_string:')
        lines.append(indent+'        if escaped: buf.append(ch); escaped=False')
        lines.append(indent+"        elif ch=='\\\\': buf.append(ch); escaped=True")
        lines.append(indent+"        elif ch=='\"': buf.append(ch); in_string=False")
        lines.append(indent+"        elif ord(ch)<32: buf.append({'\\n':'\\\\n','\\r':'\\\\r','\\t':'\\\\t'}.get(ch,'\\\\u%04x'%ord(ch)))")
        lines.append(indent+'        else: buf.append(ch)')
        lines.append(indent+'    else:')
        lines.append(indent+'        buf.append(ch)')
        lines.append(indent+"        if ch=='\"': in_string=True")
        lines.append(indent+"all_questions=json.loads(''.join(buf))")
        lines.append(indent+"H='Hybrid connectivity and architecture'; C='Core networking infrastructure'; R='Routing and traffic management'; S='Security, monitoring, and private service access'")
        lines.append(indent+'hy=[q for q in all_questions if q[\'domain\']==H]')
        lines.append(indent+'core_source=[q for q in all_questions if q[\'domain\']==C]')
        lines.append(indent+'core=[q for q in core_source if q[\'lesson\'] in (3,4)][:13]')
        lines.append(indent+'route=[dict(q,domain=R) for q in core_source if q[\'lesson\']==5][:6]')
        lines.append(indent+"tm='https://learn.microsoft.com/en-us/azure/traffic-manager/tutorial-traffic-manager-subnet-routing'")
        lines.append(indent+"route += [")
        lines.append(indent+" {'lesson':6,'domain':R,'text':'At what layer does Azure Traffic Manager make endpoint-selection decisions?','correct':'DNS','options':['DNS','TCP proxy','Layer-2 switching','BGP route reflection'],'explanation':'Traffic Manager is DNS-based global traffic distribution; it returns an endpoint and does not proxy the application flow.','source':tm},")
        lines.append(indent+" {'lesson':6,'domain':R,'text':'What is the purpose of Traffic Manager Subnet routing?','correct':'Map defined client IP ranges to specific endpoints','options':['Map defined client IP ranges to specific endpoints','Load-balance packets by five-tuple','Advertise VNet prefixes with BGP','Create private endpoints automatically'],'explanation':'Subnet routing lets a profile associate source IP ranges with preferred endpoints.','source':tm},")
        lines.append(indent+" {'lesson':6,'domain':R,'text':'After Traffic Manager answers DNS, who carries the application traffic?','correct':'The client connects directly to the selected endpoint','options':['The client connects directly to the selected endpoint','Traffic Manager proxies every packet','Azure DNS Private Resolver tunnels the flow','The authoritative DNS server becomes the TCP next hop'],'explanation':'Traffic Manager participates in DNS resolution only; the data path is directly between the client and selected endpoint.','source':tm},")
        lines.append(indent+" {'lesson':6,'domain':R,'text':'What should you validate when Subnet routing sends a client population to the wrong endpoint?','correct':'The source IP range mappings and the resolver/client source information used for DNS selection','options':['The source IP range mappings and the resolver/client source information used for DNS selection','The Application Gateway TLS certificate only','The ExpressRoute MACsec cipher','The VM accelerated networking setting'],'explanation':'Subnet routing depends on the client/source range information visible during Traffic Manager DNS selection, so incorrect mappings or source attribution change the result.','source':tm}")
        lines.append(indent+"]")
        lines.append(indent+'security=[]')
        lines.append(indent+'for lesson_id in (7,8,9,10,11,12): security.extend([q for q in all_questions if q[\'domain\']==S and q[\'lesson\']==lesson_id][:2])')
        lines.append(indent+'questions=hy+core+route+security')
        lines.append(indent+"data=data[:m.start(1)]+json.dumps(questions,ensure_ascii=False,separators=(',',':'))+data[m.end(1):]")
        lines.append(indent+"out.write_text(data,encoding='utf-8')")
    elif s.startswith("if len(current)<24:"):
        lines.append(indent+"from collections import Counter")
        lines.append(indent+"all_lesson_urls=[]")
        lines.append(indent+"for lesson_no,sec in enumerate(lessons,1):")
        lines.append(indent+"    urls=re.findall(r'href=\"(https://learn\\.microsoft\\.com/[^\"#]+)',sec)")
        lines.append(indent+"    print('LESSON_SOURCES',lesson_no,urls)")
        lines.append(indent+"    all_lesson_urls.extend(urls)")
        lines.append(indent+"print('DUPLICATE_SOURCES',[u for u,c in Counter(all_lesson_urls).items() if c>1])")
        lines.append(line)
    else:
        lines.append(line)
exec(compile('\n'.join(lines),'publish_final.py','exec'))
