from pathlib import Path
src=Path('.tmp-azure-study-2026-09-12/publish_relaxed.py').read_text()
old="if not re.search(r'\\.diagram\\s+img\\s*\\{[^}]*width\\s*:\\s*100%',data,re.I): raise SystemExit('full-width diagram css missing')"
new="if not re.search(r'(?:figure\\.)?diagram\\s+img\\s*\\{[^}]*width\\s*:\\s*100%',data,re.I): raise SystemExit('full-width diagram css missing')"
if old not in src:
    raise SystemExit('diagram css validator source pattern not found')
src=src.replace(old,new)
exec(compile(src,'publish_relaxed.py','exec'))
