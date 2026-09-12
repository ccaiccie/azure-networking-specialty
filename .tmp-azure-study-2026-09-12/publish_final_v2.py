from pathlib import Path
src=Path('.tmp-azure-study-2026-09-12/publish_final.py').read_text()
src=src.replace("for token in ('Check answer','Finish and grade','Reset quiz','function finishQuiz','function resetQuiz'):","for token in ('Check answer','Finish and grade','function finishQuiz','function resetQuiz'):")
src=src.replace("    if token not in data: raise SystemExit(f'quiz control missing: {token}')","    if token not in data: raise SystemExit(f'quiz control missing: {token}')\nif not re.search(r'<button[^>]*resetQuiz\\(\\)[^>]*>\\s*Reset(?: quiz)?\\s*</button>',data,re.I): raise SystemExit('visible reset control missing')")
exec(compile(src,'publish_final_v2.py','exec'))
