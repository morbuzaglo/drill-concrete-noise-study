"""Full pipeline of the manual: figures -> docx (pass 1) -> export + TOC page numbers -> docx (pass 2) -> final PDF."""
import subprocess, sys, pathlib
PY = sys.executable; here = pathlib.Path(__file__).parent
for step in (['make_manual_figs.py'], ['make_manual_figs2.py'], ['make_manual.py'], ['export_pdf.py', 'LS-DYNA_manual_he'], ['manual_pages.py'], ['make_manual.py'], ['export_pdf.py', 'LS-DYNA_manual_he']):
    print('>>', ' '.join(step), flush=True); subprocess.run([PY, str(here / step[0])] + step[1:], check=True, cwd=here)
