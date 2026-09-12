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
        lines.append(indent+"cp=__import__('subprocess').run(['node','-e','const questions='+raw_questions+';process.stdout.write(JSON.stringify(questions));'],text=True,capture_output=True)")
        lines.append(indent+"if cp.returncode: raise SystemExit('question JavaScript parse failed: '+cp.stderr[:700])")
        lines.append(indent+'questions=json.loads(cp.stdout)')
    else:
        lines.append(line)
exec(compile('\n'.join(lines),'publish_semantic_v2.py','exec'))
