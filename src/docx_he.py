"""Helpers for a right-to-left Hebrew technical report in python-docx (RTL paragraphs, bidi runs, RTL tables, captions, OMML)."""
import re, copy
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml, OxmlElement

HEB = re.compile('[֐-׿]')
FONT_HE = 'David'; FONT_LAT = 'Calibri'
NAVY = RGBColor(0x12, 0x26, 0x4A)


def new_document():
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2); sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(2.0)
    st = d.styles['Normal']; st.font.name = FONT_LAT; st.font.size = Pt(11.5)
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi'): rf.set(qn(a), FONT_LAT)
    for a in ('w:cs', 'w:eastAsia'): rf.set(qn(a), FONT_HE)
    szcs = OxmlElement('w:szCs'); szcs.set(qn('w:val'), '23'); rpr.append(szcs)
    for name, size, color in (('Heading 1', 17, NAVY), ('Heading 2', 14, NAVY), ('Heading 3', 12, NAVY)):
        h = d.styles[name]; h.font.name = FONT_HE; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = color
        r = h.element.get_or_add_rPr(); rf = r.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); r.append(rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), FONT_HE)
        for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
            if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
        szc = OxmlElement('w:szCs'); szc.set(qn('w:val'), str(size * 2)); r.append(szc)
        bcs = OxmlElement('w:bCs'); r.append(bcs)
    # proofing: Hebrew for complex-script text, no spelling/grammar squiggles in a generated technical document
    st_el = d.styles.element
    dd = st_el.find(qn('w:docDefaults'))
    if dd is not None:
        rpd = dd.find(qn('w:rPrDefault'))
        if rpd is not None:
            rp = rpd.find(qn('w:rPr'))
            if rp is not None:
                for old in rp.findall(qn('w:lang')): rp.remove(old)
                lg = OxmlElement('w:lang'); lg.set(qn('w:val'), 'en-US'); lg.set(qn('w:eastAsia'), 'he-IL'); lg.set(qn('w:bidi'), 'he-IL'); rp.append(lg)
    sett = d.settings.element
    anchor = next((c for c in sett if c.tag in (qn('w:proofState'), qn('w:defaultTabStop'))), None)
    for tag in ('w:hideSpellingErrors', 'w:hideGrammaticalErrors'):
        if sett.find(qn(tag)) is None:
            el = OxmlElement(tag)
            if anchor is not None: anchor.addprevious(el)
            else: sett.append(el)
    return d


def _bidi(p, rtl=True):
    ppr = p._p.get_or_add_pPr()
    if rtl and ppr.find(qn('w:bidi')) is None:
        b = OxmlElement('w:bidi'); ppr.insert(0, b)


def _run(p, text, bold=False, italic=False, size=None, color=None, rtl=False, mono=False):
    r = p.add_run(text)
    r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color is not None: r.font.color.rgb = color
    rpr = r._r.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
    if mono:
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'): rf.set(qn(a), 'Consolas')
    elif rtl:
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'): rf.set(qn(a), FONT_HE)
    else:
        rf.set(qn('w:ascii'), FONT_LAT); rf.set(qn('w:hAnsi'), FONT_LAT); rf.set(qn('w:cs'), FONT_LAT)
    if rtl:
        rpr.append(OxmlElement('w:rtl'))
        if bold: rpr.append(OxmlElement('w:bCs'))
        if size:
            szcs = OxmlElement('w:szCs'); szcs.set(qn('w:val'), str(int(size * 2))); rpr.append(szcs)
    if mono: rpr.append(OxmlElement('w:noProof'))
    lang = OxmlElement('w:lang'); lang.set(qn('w:val'), 'en-US'); lang.set(qn('w:bidi'), 'he-IL'); rpr.append(lang)
    return r


LRM = '\u200e'
_ALN = re.compile('[A-Za-z0-9\u0370-\u03ff]')
_TAILSYM = '%\u00b0\u00b2\u00b3\u00b9\u207b'       # % degree squared cubed ...
_SIGNS = '+\u2212\u00b1'


def _core_bounds(seg):
    """Index range [i, j) of the left-to-right island inside a non-Hebrew stretch: from the first to the last Latin/digit,
    extended by a sign before a number, unit symbols after it, and the brackets needed to balance the island.
    Everything outside (spaces, commas, a hyphen after a Hebrew prefix, unbalanced brackets) is emitted as an RTL run."""
    ms = list(_ALN.finditer(seg))
    i, j = ms[0].start(), ms[-1].end()
    while i > 0 and seg[i - 1] in _SIGNS: i -= 1                       # sign directly before the number
    if i > 0 and seg[i - 1] == '-' and i - 1 > 0 and seg[i - 2].isspace() and seg[i].isdigit(): i -= 1   # minus after a space
    while j < len(seg) and seg[j] in _TAILSYM: j += 1
    depth = 0; need_left = 0
    for ch in seg[i:j]:
        if ch in '([{': depth += 1
        elif ch in ')]}':
            if depth: depth -= 1
            else: need_left += 1
    need_right = depth
    while need_left and i > 0 and seg[i - 1] in '([{': i -= 1; need_left -= 1
    while need_right and j < len(seg) and seg[j] in ')]}': j += 1; need_right -= 1
    return i, j


_SUBRE = re.compile('(?<![A-Za-z0-9_.])([A-Za-zΩω])_([A-Za-z0-9]{1,4})(?![A-Za-z0-9_.(])')
_NBSP = ' '
_UNITS = re.compile(r'(\d) (?=(?:Hz|kHz|dB|mm|cm|m/s|N·m|kg/m³|rad/s|kW|GPa|µPa|ms|Pa|rpm|m|N|W|s)(?![A-Za-z0-9]))')


def _island(p, text, b, italic, size, color):
    """Left-to-right island; X_sub patterns (single letter + short subscript) become real subscripts."""
    pos = 0
    for m in _SUBRE.finditer(text):
        if m.start() > pos: _run(p, text[pos:m.start()], bold=b, italic=italic, size=size, color=color, rtl=False)
        _run(p, m.group(1), bold=b, italic=italic, size=size, color=color, rtl=False)
        r = _run(p, m.group(2), bold=b, italic=italic, size=size, color=color, rtl=False); r.font.subscript = True
        pos = m.end()
    if pos < len(text): _run(p, text[pos:], bold=b, italic=italic, size=size, color=color, rtl=False)


def _ltr(p, seg, b, italic, size, color):
    """Non-Hebrew stretch between two Hebrew stretches. Latin/numbers/formulas become one isolated LTR island (LRM on both sides);
    all other characters (spaces, punctuation, brackets, a hyphen attached to a Hebrew prefix) become RTL runs, so a closing bracket or
    comma stays on the Hebrew side of the island where it belongs."""
    if not _ALN.search(seg):
        _run(p, seg, bold=b, italic=italic, size=size, color=color, rtl=True); return
    i, j = _core_bounds(seg)
    if i: _run(p, seg[:i], bold=b, italic=italic, size=size, color=color, rtl=True)
    _island(p, LRM + seg[i:j] + LRM, b, italic, size, color)
    if j < len(seg): _run(p, seg[j:], bold=b, italic=italic, size=size, color=color, rtl=True)


_SPLIT = re.compile(r'([֐-׿][֐-׿\s,.;:!?־"\'()\-–]*[֐-׿]|[֐-׿])')


def add_text(p, text, bold=False, italic=False, size=None, color=None):
    """Mixed Hebrew/Latin text: Hebrew stretches become RTL runs; everything else (Latin, digits, units, formulas) LTR runs.
    Inline markers: **bold**, `mono`."""
    text = _UNITS.sub(lambda m: m.group(1) + _NBSP, text)
    parts = re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text)
    for part in parts:
        if not part: continue
        b = bold; mono = False
        if part.startswith('**') and part.endswith('**'): part = part[2:-2]; b = True
        elif part.startswith('`') and part.endswith('`'): part = part[1:-1]; mono = True
        if mono: _run(p, part, bold=b, italic=italic, size=size, color=color, mono=True); continue
        pos = 0
        for m in _SPLIT.finditer(part):
            if m.start() > pos: _ltr(p, part[pos:m.start()], b, italic, size, color)
            _run(p, m.group(0), bold=b, italic=italic, size=size, color=color, rtl=True)
            pos = m.end()
        if pos < len(part): _ltr(p, part[pos:], b, italic, size, color)
    return p


def para(d, text='', style=None, align='right', bold=False, italic=False, size=None, color=None, space_after=6, keep=False):
    p = d.add_paragraph(style=style); _bidi(p)
    pf = p.paragraph_format; pf.space_after = Pt(space_after); pf.space_before = Pt(0); pf.line_spacing = 1.15
    if keep: pf.keep_with_next = True
    p.alignment = {'right': WD_ALIGN_PARAGRAPH.RIGHT, 'center': WD_ALIGN_PARAGRAPH.CENTER, 'left': WD_ALIGN_PARAGRAPH.LEFT, 'justify': WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
    # for bidi paragraphs python-docx 'right' means start-side visually mirrored; in a bidi paragraph LEFT == start (right on screen)
    if align == 'right': p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif align == 'left': p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if text: add_text(p, text, bold=bold, italic=italic, size=size, color=color)
    return p


def heading(d, text, level=1):
    text = re.sub(r'^(\d+)\.\s', lambda m: m.group(1) + '  ', text)
    p = d.add_heading('', level=level); _bidi(p); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(12 if level == 1 else 8); p.paragraph_format.space_after = Pt(5)
    add_text(p, text); return p


def bullets(d, items, size=None):
    for it in items:
        p = para(d, '', space_after=3)
        ppr = p._p.get_or_add_pPr(); ind = OxmlElement('w:ind'); ind.set(qn('w:right'), '360'); ind.set(qn('w:hanging'), '280'); ppr.append(ind)
        add_text(p, '•  ' + it, size=size)


def _shade(cell, hexcolor):
    tcpr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hexcolor); tcpr.append(shd)


def table(d, header, rows, widths=None, size=9.5, header_fill='12264A', zebra=True, align_num='center'):
    t = d.add_table(rows=1, cols=len(header)); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = t._tbl.tblPr
    tblPr.append(OxmlElement('w:bidiVisual'))
    borders = parse_xml('<w:tblBorders %s><w:top w:val="single" w:sz="6" w:color="12264A"/><w:bottom w:val="single" w:sz="6" w:color="12264A"/><w:insideH w:val="single" w:sz="2" w:color="C9D1DB"/></w:tblBorders>' % nsdecls('w'))
    tblPr.append(borders)
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ''; p = c.paragraphs[0]; _bidi(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_text(p, h, bold=True, size=size, color=RGBColor(255, 255, 255)); _shade(c, header_fill)
    trpr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); trpr.append(th)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            c = cells[i]; c.text = ''; p = c.paragraphs[0]; _bidi(p); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            add_text(p, str(v), size=size)
            if zebra and ri % 2 == 1: _shade(c, 'EEF3F8')
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(d, path, width_cm, caption, counter):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    counter['fig'] += 1
    c = para(d, f'איור {counter["fig"]}: ' + caption, align='center', size=9.5, italic=False, space_after=10)
    return c


def table_caption(d, text, counter):
    counter['tab'] += 1
    return para(d, f'טבלה {counter["tab"]}: ' + text, align='right', size=10, bold=True, space_after=3, keep=True)


# ------------------------------------------------------------------ OMML equations
M = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'


def _mr(t, sty=None):
    s = f'<m:rPr><m:sty m:val="{sty}"/></m:rPr>' if sty else ''
    return f'<m:r>{s}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr><m:t xml:space="preserve">{t}</m:t></m:r>'


def _sub(base, sub, sty=None):
    return f'<m:sSub><m:e>{_mr(base, sty)}</m:e><m:sub>{_mr(sub, "p")}</m:sub></m:sSub>'


def _frac(n, dn):
    return f'<m:f><m:num>{n}</m:num><m:den>{dn}</m:den></m:f>'


def equation(d, omml_inner, number=None):
    """Display equation: OMML inside its own paragraph (LTR math), optional number."""
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(6)
    x = f'<m:oMathPara {M} {nsdecls("w")}><m:oMath>{omml_inner}</m:oMath></m:oMathPara>'
    p._p.append(parse_xml(x))
    return p


EQ = {
    'H': _sub('H', 'p,F') + _mr('(f)=') + _frac(_mr('p(f)'), _mr('F(f)')),
    'SPL': _sub('L', 'p') + _mr('=10') + _mr('lg', 'p') + '<m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/></m:dPr><m:e>' + _frac(_sub('p', 'rms') + '<m:sSup><m:e></m:e><m:sup>' + _mr('2') + '</m:sup></m:sSup>', '<m:sSup><m:e>' + _sub('p', '0') + '</m:e><m:sup>' + _mr('2') + '</m:sup></m:sSup>') + '</m:e></m:d>' + _mr(',   ') + _sub('p', '0') + _mr('=20 µPa'),
    'BAND': '<m:sSup><m:e>' + _sub('p', 'rms,b') + '</m:e><m:sup>' + _mr('2') + '</m:sup></m:sSup>' + _mr('=') + '<m:nary><m:naryPr><m:chr m:val="∫"/></m:naryPr><m:sub>' + _sub('f', '1') + '</m:sub><m:sup>' + _sub('f', '2') + '</m:sup><m:e>' + '<m:sSup><m:e>' + _mr('|') + _sub('H', 'p,F') + _mr('(f)|') + '</m:e><m:sup>' + _mr('2') + '</m:sup></m:sSup>' + _sub('S', 'FF') + _mr('(f) df') + '</m:e></m:nary>',
    'SSD': '<m:d><m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr><m:e>' + _mr('K(1+iη)+iωC(ω)−') + '<m:sSup><m:e>' + _mr('ω') + '</m:e><m:sup>' + _mr('2') + '</m:sup></m:sSup>' + _mr('M') + '</m:e></m:d>' + _mr('u(ω)=F'),
    'BIE': _mr('½p(x)−') + '<m:nary><m:naryPr><m:chr m:val="∫"/></m:naryPr><m:sub>' + _mr('Γ') + '</m:sub><m:sup></m:sup><m:e>' + _mr('p(y)') + _frac(_mr('∂G(x,y)'), _mr('∂n(y)')) + _mr('dΓ=iωρ') + _sub('', '0') + '</m:e></m:nary>' + '<m:nary><m:naryPr><m:chr m:val="∫"/></m:naryPr><m:sub>' + _mr('Γ') + '</m:sub><m:sup></m:sup><m:e>' + _mr('G(x,y)') + _sub('v', 'n') + _mr('(y)dΓ') + '</m:e></m:nary>',
    'SCALE': _mr('Δ') + _sub('L', 'p') + _mr('=20') + _mr('lg', 'p') + _mr('2=6.02 dB'),
}
