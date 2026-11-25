"""Word COM: update fields (TOC), save the docx and export a PDF. usage: python export_pdf.py [basename=drill_noise_report_he]"""
import win32com.client, pathlib, sys
name = sys.argv[1] if len(sys.argv) > 1 else 'drill_noise_report_he'
r = pathlib.Path(__file__).resolve().parents[1] / 'report'
w = win32com.client.Dispatch('Word.Application'); w.Visible = False
d = w.Documents.Open(str(r / f'{name}.docx'))
if d.TablesOfContents.Count: d.TablesOfContents(1).Update()
d.Fields.Update(); d.Save()
d.ExportAsFixedFormat(str(r / f'{name}.pdf'), 17)
print('pages', d.ComputeStatistics(2)); d.Close(False); w.Quit()
