"""Word COM: read the page number of every Heading 1/2 of the manual (in order) and store it in report/toc_pages[_solid].json for the static TOC.
usage: python manual_pages.py [suffix]     suffix '' (version A) or '_solid' (version B)"""
import win32com.client, pathlib, json, sys
suf = sys.argv[1] if len(sys.argv) > 1 else ''
r = pathlib.Path(__file__).resolve().parents[1] / 'report'
w = win32com.client.Dispatch('Word.Application'); w.Visible = False
d = w.Documents.Open(str(r / f'LS-DYNA_manual{suf}_he.docx'))
pages = []; first = True
for p in d.Paragraphs:
    if p.OutlineLevel in (1, 2) and p.Range.Text.strip():
        if first: first = False; continue          # the "table of contents" heading itself
        pages.append(p.Range.Information(3))
(r / f'toc_pages{suf}.json').write_text(json.dumps(pages)); print(len(pages), 'headings, last page', pages[-1])
d.Close(False); w.Quit()
