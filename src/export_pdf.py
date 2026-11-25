import win32com.client, pathlib, sys
r = pathlib.Path(__file__).resolve().parents[1] / 'report'
w = win32com.client.Dispatch('Word.Application'); w.Visible = False
d = w.Documents.Open(str(r / 'drill_noise_report_he.docx'))
d.ExportAsFixedFormat(str(r / 'drill_noise_report_he.pdf'), 17)
print('pages', d.ComputeStatistics(2)); d.Close(False); w.Quit()
