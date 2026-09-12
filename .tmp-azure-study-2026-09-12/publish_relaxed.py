from pathlib import Path
src=Path('.tmp-azure-study-2026-09-12/publish.py').read_text()
old="if not re.search(r'<h3>Architecture</h3>.*?<figure class=\"diagram\">\\s*<img[^>]+\\.svg',sec,re.S|re.I): raise SystemExit(f'L{n} architecture diagram placement')"
new="if not re.search(r'<h3>Architecture[^<]*</h3>.*?src=\"images/[^\"]+\\.svg\"',sec,re.S|re.I): raise SystemExit(f'L{n} architecture diagram placement')"
if old not in src:
    raise SystemExit('architecture validator source pattern not found')
src=src.replace(old,new)
exec(compile(src,'publish.py','exec'))
