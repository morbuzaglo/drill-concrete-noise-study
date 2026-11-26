"""Full pipeline of the manual: figures -> docx (pass 1) -> export + TOC page numbers -> docx (pass 2) -> final PDF.
usage: python build_manual.py [solid]     'solid' builds version B (soil as a solid block) -> LS-DYNA_manual_solid_he"""
import subprocess, sys, os, pathlib
PY = sys.executable; here = pathlib.Path(__file__).parent
solid = len(sys.argv) > 1 and sys.argv[1] == 'solid'; suf = '_solid' if solid else ''
env = dict(os.environ, MANUAL_SOLID='1' if solid else '0')
steps = ([] if solid else [['make_manual_figs.py'], ['make_manual_figs2.py']]) + [['make_manual.py'], ['export_pdf.py', f'LS-DYNA_manual{suf}_he'], ['manual_pages.py', suf], ['make_manual.py'], ['export_pdf.py', f'LS-DYNA_manual{suf}_he']]
for step in steps:
    print('>>', ' '.join(step), flush=True); subprocess.run([PY, str(here / step[0])] + step[1:], check=True, cwd=here, env=env)
