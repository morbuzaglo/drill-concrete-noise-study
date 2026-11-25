"""Hebrew (RTL) theory + practice manual: structure-borne noise simulation with LS-DYNA (SSD + acoustic BEM).
Figures are SVG (with PNG fallback, OOXML svgBlip). Code excerpts are read from the real decks in lsdyna/t10_bur."""
import pathlib, datetime
from docx.opc.part import Part
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx_he import *
from docx_he import _mr, _sub, _frac, _bidi, _shade

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / 'figures' / 'manual'; OUT = ROOT / 'report'; OUT.mkdir(exist_ok=True)
DECK = ROOT / 'lsdyna' / 't10_bur'
cnt = {'fig': 0, 'tab': 0}
_svg_n = [0]


# ------------------------------------------------------------------ helpers
def fig(d, name, width_cm, caption):
    png = FIG / f'{name}.fallback.png'; svg = FIG / f'{name}.svg'
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
    run = p.add_run(); run.add_picture(str(png), width=Cm(width_cm))
    _svg_n[0] += 1
    part = Part(PackURI(f'/word/media/figure{_svg_n[0]}.svg'), 'image/svg+xml', svg.read_bytes(), d.part.package)
    rid = d.part.relate_to(part, RT.IMAGE)
    blip = run._r.xpath('.//a:blip')[0]
    ext = parse_xml('<a:extLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">'
                    '<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="%s"/></a:ext></a:extLst>' % rid)
    blip.append(ext)
    cnt['fig'] += 1
    para(d, f'איור {cnt["fig"]}: ' + caption, align='center', size=9.5, space_after=10)


def code(d, text, size=8.5, title=None):
    if title: para(d, title, size=9.5, bold=True, space_after=2, keep=True)
    t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t._tbl.tblPr.append(parse_xml('<w:tblBorders %s><w:top w:val="single" w:sz="4" w:color="9AA7B8"/><w:left w:val="single" w:sz="18" w:color="0F8B8D"/><w:bottom w:val="single" w:sz="4" w:color="9AA7B8"/><w:right w:val="single" w:sz="4" w:color="9AA7B8"/></w:tblBorders>' % nsdecls('w')))
    c = t.rows[0].cells[0]; _shade(c, 'F3F6F9'); c.width = Cm(16.4)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
    lines = text.rstrip('\n').split('\n')
    for i, ln in enumerate(lines):
        r = p.add_run(ln); r.font.size = Pt(size); r.font.name = 'Consolas'
        rpr = r._r.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), 'Consolas')
        if i < len(lines) - 1: r.add_break()
    d.add_paragraph().paragraph_format.space_after = Pt(3)


def grab(fname, keyword, n, skip=0):
    lines = (DECK / fname).read_text().split('\n'); idx = [i for i, l in enumerate(lines) if l.startswith(keyword)][skip]
    return '\n'.join(l.rstrip() for l in lines[idx:idx + n + 1])


def eq(d, inner):
    equation(d, inner)


def T(d, caption, header, rows, widths, size=9.5):
    table_caption(d, caption, cnt); table(d, header, rows, widths=widths, size=size)


def note(d, text, kind='טיפ'):
    t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t._tbl.tblPr.append(OxmlElement('w:bidiVisual'))
    col = {'טיפ': 'E3F4EE', 'אזהרה': 'FBE3E1', 'הערה': 'FFF4D6'}[kind]
    c = t.rows[0].cells[0]; _shade(c, col); p = c.paragraphs[0]; _bidi(p); p.paragraph_format.space_after = Pt(2)
    add_text(p, f'**{kind}.** ' + text, size=10.5)
    d.add_paragraph().paragraph_format.space_after = Pt(3)


def _fld(p, kind=None, instr=None, text=None, size=None):
    r = p.add_run()
    if size: r.font.size = Pt(size)
    if kind:
        fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), kind); r._r.append(fc)
    if instr:
        it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = instr; r._r.append(it)
    if text:
        tt = OxmlElement('w:t'); tt.text = text; r._r.append(tt)


def add_toc(d):
    p = d.add_paragraph()
    _fld(p, 'begin'); _fld(p, instr=r' TOC \o "1-2" \h \z \u '); _fld(p, 'separate'); _fld(p, text='TOC'); _fld(p, 'end')


def footer_page_number(d):
    p = d.sections[0].footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fld(p, 'begin', size=9); _fld(p, instr=' PAGE ', size=9); _fld(p, 'separate', size=9); _fld(p, text='1', size=9); _fld(p, 'end', size=9)


def S(x): return _mr(x)


def sup(base, e): return f'<m:sSup><m:e>{_mr(base)}</m:e><m:sup>{_mr(e)}</m:sup></m:sSup>'


# ------------------------------------------------------------------ document
def build():
    d = new_document(); footer_page_number(d)
    para(d, 'מדריך תיאורטי ומעשי', align='center', bold=True, size=24, color=NAVY, space_after=2)
    para(d, 'סימולציית רעש מבני עם LS-DYNA', align='center', bold=True, size=20, color=NAVY, space_after=2)
    para(d, 'תגובה בתחום התדר (SSD) וקרינה אקוסטית (BEM): מהתיאוריה ועד קובץ ה-k, הרצה ופענוח התוצאות', align='center', size=13, space_after=4)
    para(d, 'המקרה הלימודי: קידוח בלוח בטון, עובי 100 ו-200 mm, חשוף או קבור חלקית באדמה', align='center', size=11.5, space_after=4)
    para(d, f'תאריך: {datetime.date.today().strftime("%d.%m.%Y")}. המדריך מלווה את הדוח "רעש מבני מקידוח בבטון" ואת קבצי ההרצה בתיקייה lsdyna.', align='center', size=10, space_after=10)
    heading(d, 'תוכן העניינים', 1); add_toc(d)
    d.add_page_break()

    # ============================================================ 0
    heading(d, '0. איך להשתמש במדריך', 1)
    para(d, 'המדריך בנוי משני חלקים. **חלק א** הוא התיאוריה: מה קורה פיזיקלית כשכוח משתנה בזמן מפעיל לוח בטון, איך המבנה מגיב, ואיך הרטט הופך ללחץ אקוסטי. **חלק ב** הוא המעשה: כל שלב מוגדר ב-LS-DYNA, עם מילות המפתח האמיתיות, הכרטיסים והשדות, קטעים מקובץ ה-k שהרצנו בפועל, פקודת ההרצה, קבצי הפלט ופענוח התוצאות. בסוף יש טבלת שגיאות אמיתיות שנתקלנו בהן ופתרונן, רשימת בדיקה וטבלת מילות מפתח.')
    para(d, 'כל מה שמופיע כקטע קוד הוא מהמחקר. הוא רץ בגרסה R14 של Ansys LS-DYNA (v252) עד "Normal termination". היכן שלא אימתנו התנהגות מול הפתרן, כתבנו זאת במפורש.')
    fig(d, 'f09_workflow', 15.5, 'תהליך העבודה כולו: קובץ קלט אחד, שלושה שלבי חישוב, קבצי פלט ופוסט-פרוססינג.')
    T(d, 'מפת הקריאה', ['אם אתם רוצים…', 'קראו'], [
        ['להבין למה לוח דק רועש יותר', 'פרקים 1 עד 4'],
        ['לבנות מודל מאפס ב-LS-DYNA', 'פרקים 6 עד 12'],
        ['להריץ ולפענח תוצאות', 'פרקים 13 ו-14'],
        ['לתקן שגיאה בלוג', 'פרק 15 ונספח א'],
        ['לוודא שהמודל נכון', 'פרקים 5 ו-16'],
    ], [8.0, 7.0])

    # ============================================================ PART A
    para(d, '')
    heading(d, 'חלק א: תיאוריה', 1)
    heading(d, '1. רעש מבני: מקור, מבנה, קרינה, מקלט', 1)
    para(d, 'רעש מבני (structure-borne noise) הוא קול שמקורו ברטט של גוף מוצק. מקדחה לא "מרעישה" בעיקר דרך הלהב באוויר. היא מפעילה על הבטון כוח משתנה, הבטון רוטט, ומשטחי הלוח הגדולים דוחפים את האוויר ויוצרים גל קול. את התהליך כולו אפשר לפרק לשלושה חוליות בטור.')
    fig(d, 'f01_chain', 15.5, 'שרשרת הרעש המבני. כל חוליה מחושבת בשיטה אחרת ואפשר לבדוק אותה בנפרד.')
    bullets(d, [
        '**מקור:** כוח F(f) שמעביר הקידוח לבטון, בנקודה או על טבעת. במחקר הגדרנו עומס יחידה: 1 N צירי, או 1 N·m פיתול.',
        '**מבנה:** תגובת הלוח והאדמה לכוח, כלומר מהירות המשטח v(f). פותרים בשיטת האלמנטים הסופיים בתחום התדר.',
        '**קרינה:** המרה של מהירות משטח ללחץ באוויר p(f). פותרים בשיטת האלמנטים בגבול (BEM).',
        '**מקלט:** לחץ במיקרופון. מגדירים אותו כנקודת שדה (field point) מחוץ לגוף.'])
    heading(d, '1.1 פונקציית תמסורת ורמות', 2)
    para(d, 'מכיוון שהמערכת לינארית, אפשר לחשב את התגובה ליחידת כוח אחת ולהכפיל בספקטרום הכוח האמיתי אחר כך. זו פונקציית התמסורת לחץ-כוח. היא נמדדת ב-Pa/N ומתארת את המערכת בלי קשר למקדחה הספציפית:', keep=True)
    equation(d, EQ['H'])
    para(d, 'לחץ אקוסטי מבוטא כרמה ב-dB ביחס ללחץ ייחוס:', keep=True)
    equation(d, EQ['SPL'])
    para(d, 'כשיודעים את ספקטרום הצפיפות הספקטרלית של הכוח S_FF(f), המרובע הממוצע של הלחץ בפס שבין f₁ ל-f₂ הוא:', keep=True)
    equation(d, EQ['BAND'])
    heading(d, '1.2 פסי אוקטבה', 2)
    para(d, 'בפסי אוקטבה בסיס 2 גבולות הפס הם fc/√2 ו-fc·√2, ומרכזי הפסים 31.5, 63, 125, 250, 500, 1000, 2000, 4000 ו-8000 Hz. הפסים שבהם הלוח הקרין ביעילות במחקר הם 63 עד 1000 Hz, ולכן חישבנו בתחום 44.2 עד 1414 Hz.')
    fig(d, 'f02_octave', 14.5, 'פסי אוקטבה. הפסים שנפתרו במחקר מסומנים בירוק-כחול.')

    heading(d, '2. דינמיקה מבנית בתחום התדר', 1)
    heading(d, '2.1 דרגת חופש אחת', 2)
    para(d, 'נתחיל במסה על קפיץ ובולם, שהיא אבן הבניין של כל ניתוח מודאלי. כוח הרמוני F·e^{iωt} מפעיל מסה m, קשיחות k ובלימה c:', keep=True)
    equation(d, S('m ẍ + c ẋ + k x = F e^{iωt}') + S(' ⟹ ') + _frac(S('x'), S('F')) + S(' = ') + _frac(S('1'), S('k − ω²m + iωc')))
    para(d, 'משרעת התגובה מגיעה לשיא בתהודה, ω=ωₙ=√(k/m). גובה השיא הוא בקירוב 1/(2ζ), כאשר ζ=c/(2√(km)) הוא יחס הבלימה. בבטון ζ קטן מאוד, בסדר גודל 0.5% עד 2%, ולכן השיאים חדים. בתדרים הרחוקים מהתהודה הבלימה כמעט לא משפיעה, ובתהודה היא הגורם היחיד שקובע את משרעת הרטט. הפאזה יורדת מ-0° ל-180° מינוס בקפיצה שחדה ככל ש-ζ קטן.')
    fig(d, 'f03_sdof', 12.5, 'תגובת דרגת חופש אחת לפי יחס הבלימה. הבלימה קובעת רק את גובה השיא ואת חדות הקפיצה בפאזה.')
    heading(d, '2.2 מבנה בעל דרגות חופש רבות: מודים', 2)
    para(d, 'מבנה מרובה דרגות חופש מתואר במטריצות מסה M, קשיחות K ובלימה C. המשוואה בתחום התדר היא:', keep=True)
    equation(d, EQ['SSD'])
    para(d, 'פתרון ישיר דורש היפוך מטריצה בכל תדר. הדרך היעילה היא לנצל את המודים. מוצאים את הערכים העצמיים ωₙ ואת וקטורי המוד φₙ מתוך (K − ωₙ²M)φₙ = 0, מנרמלים את המודים כך ש-φₙᵀMφₙ=1, ומציבים u = Σ qₙφₙ. כל מוד מתנהג כדרגת חופש אחת:', keep=True)
    equation(d, S('q̈ₙ + 2ζₙωₙq̇ₙ + ωₙ²qₙ = φₙᵀF'))
    para(d, 'בתחום התדר הפתרון הוא סכום של תרומות המודים, וזה בדיוק מה ש-LS-DYNA מבצע ב-*FREQUENCY_DOMAIN_SSD:', keep=True)
    equation(d, S('u(ω) = ') + '<m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr><m:sub>' + S('n') + '</m:sub><m:sup></m:sup><m:e>' + _frac(S('φₙ (φₙᵀF)'), S('ωₙ² − ω² + 2iζₙωₙω')) + '</m:e></m:nary>')
    bullets(d, [
        '**חישוב יעיל:** מחשבים ערכים עצמיים פעם אחת, ואחר כך כל תדר הוא חישוב סקלרי פשוט לכל מוד.',
        '**הבנה פיזיקלית:** אפשר לראות איזה מוד אחראי לכל שיא, ואיזה מוד "יושב" על צומת העומס ולכן לא מתעורר.',
        '**חיסרון:** קוטעים את הסכום. חייבים לכלול מודים עד מעל התדר העליון המעניין, אחרת חסר ל-u(ω) החלק האלסטי של המודים העליונים (השארית הסטטית).'])
    fig(d, 'f04_modes', 13.5, 'צורות מודים של לוח מרובע נשען חופשית. ככל שהמוד גבוה יותר, יש יותר קווי צומת וגודל האלמנט חייב להיות קטן יותר.')
    heading(d, '2.3 מודל הבלימה', 2)
    T(d, 'דרכים להגדיר בלימה בניתוח תדר', ['מודל', 'הגדרה', 'מתי משתמשים'], [
        ['בלימה מודאלית קבועה', 'ζₙ זהה לכל המודים (במחקר ζ=0.01)', 'ברירת מחדל לבטון: אין נתוני בלימה מפורטים'],
        ['בלימה היסטרטית (איבוד)', 'η, נכנס כ-K(1+iη); η=2ζ בתהודה', 'ניסוי שמדווח על מקדם איבוד'],
        ['בלימת Rayleigh', 'C=αM+βK; ζₙ=α/(2ωₙ)+βωₙ/2', 'הרצות בזמן (explicit), לא לבלימה קבועה'],
        ['בולמים נקודתיים', 'דשפוטים בתמיכה, כמו האדמה', 'בלימה שמקורה בקרינה לאדמה'],
    ], [3.8, 6.2, 5.8])
    heading(d, '2.4 כמה אלמנטים צריך', 2)
    para(d, 'צורת המוד צריכה להיות מתוארת היטב ברשת. כלל האצבע הוא לפחות 6 אלמנטים לאורך גל. אורך הגל של כפיפה בלוח הוא λ_b = 2π/k_b, כאשר k_b = (ω²ρh/D)^{1/4} ו-D = Eh³/(12(1−ν²)) הוא קשיחות הכפיפה. עבור 100 mm בטון ב-1414 Hz מתקבל λ_b≈0.68 m, כלומר גודל אלמנט מרבי של כ-0.11 m. האלמנט שבחרנו, 0.05 m, מספק מרווח בטיחות. לאקוסטיקה אורך הגל הוא c/f, ולכן הרשת האקוסטית נדרשת להיות עדינה יותר בתדרים גבוהים: ב-1414 Hz האורך הוא 0.24 m, כלומר פאנל של 0.04 m.')
    fig(d, 'f05_meshrule', 13.0, 'גודל אלמנט מרבי כפונקציה של התדר. הפאנל האקוסטי ב-0.10 m מספיק רק בתחום הנמוך. מעל כ-600 Hz עוברים ל-0.05 m.')

    heading(d, '3. האדמה כעכבה', 1)
    para(d, 'הלוח הקבור נוגע באדמה, והאדמה גם מקשיחה וגם מרחיקה אנרגיה (קרינה לאדמה). בחצי-מרחב אמיתי היינו צריכים רשת של אדמה שמתפרשת על פני עשרות מטרים, וגבולות שלא מחזירים גלים. במקום זה מילאנו את התפקיד בעזרת קפיצים ובולמים (מודל Winkler עם בולמי Lysmer) על פני הלוח הקבורים. לכל יחידת שטח:', keep=True)
    equation(d, S('kₙ = ρc_p²/L,   kₜ = G/L,   cₙ = ρc_p,   cₜ = ρV_s'))
    para(d, 'כאן ρ הצפיפות, V_s מהירות גל גזירה, G=ρV_s², c_p=V_s√(2(1−ν)/(1−2ν)), ו-L אורך ייחוס. הבולם ρc הוא האימפדנס האופייני של גל בחומר: אנרגיה שזורמת אליו לא חוזרת, וזה מה שקורה בקרינה לאדמה. הערכים ליחידת שטח מוכפלים בשטח המשפיע של כל צומת.')
    fig(d, 'f06_soil', 14.5, 'שני מודלים לאדמה. המחקר השתמש בקפיצים ובולמים (משמאל). המודל מימין מדויק יותר ויקר בהרבה.')
    note(d, 'אורך הייחוס L=1 m הוא בחירת מודל ואין לו בסיס פיזיקלי. זו הסיבה שהתוצאות בתדרים נמוכים (63 ו-125 Hz) רגישות להנחות האדמה: שינוי Vs ב-2.4 עד 4 dB משנה את הסימן של השפעת הקבורה. כשהאדמה חשובה, בנו תחום אדמה אמיתי עם גבולות בולעים.', 'אזהרה')

    heading(d, '4. אקוסטיקה: קרינה מלוח רוטט', 1)
    heading(d, '4.1 למה לוח דק רועש יותר: תדר ההתלכדות', 2)
    para(d, 'לוח מרוטט בגל כפיפה שמהירותו תלויה בתדר: c_b = (ω²D/ρh)^{1/4}. כשגל הכפיפה איטי מהקול, האוויר זורם בין אזורים סמוכים של הלוח שנעים בפאזה הפוכה, ולכן הקרינה חלשה. כשהוא מהיר מהקול, אורך הגל בלוח גדול מאורך הגל באוויר והלוח קורן ביעילות. התדר שבו שתי המהירויות שוות הוא תדר ההתלכדות (coincidence):', keep=True)
    equation(d, S('f_c = ') + _frac(S('c²'), S('2π')) + '<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>' + _frac(S('ρh'), S('D')) + '</m:e></m:rad>')
    para(d, 'עבור הבטון שלנו מתקבל fc≈180 Hz ללוח של 100 mm וכ-90 Hz ללוח של 200 mm. שני התדרים נמצאים בתוך תחום החישוב, ולכן הקרינה משתנה בו באופן מורכב: מעל fc הלוח קורן ביעילות מלאה, ומתחת קורנים בעיקר הקצוות והפינות. לוח עבה יותר מסיט את fc למטה, ובנוסף הוא קשיח יותר ולכן רוטט פחות באותו כוח. שני הגורמים מתיישבים עם ממצא המחקר: הלוח העבה שקט יותר ב-3 עד 13 dB.')
    fig(d, 'f07_coincidence', 13.0, 'מהירות גל כפיפה מול מהירות הקול. נקודות החיתוך הן תדרי ההתלכדות של שני העוביים.')
    heading(d, '4.2 שיטת האלמנטים בגבול (BEM)', 2)
    para(d, 'בתחום האוויר הלחץ מקיים את משוואת Helmholtz, ∇²p + k²p = 0 עם k=ω/c, ותנאי קרינה בהסתר (Sommerfeld). על פני המבנה Γ נתונה מהירות הנורמל v_n, והתנאי הוא ∂p/∂n = −iωρ₀vₙ. במקום לחלק את כל האוויר לרשת, BEM מבטא את הלחץ בכל נקודה כאינטגרל על המשטח Γ בלבד:', keep=True)
    equation(d, EQ['BIE'])
    para(d, 'לכן רשת BEM היא רק משטח דו-ממדי, ונקודות שדה הן נקודות סתם במרחב. בשיטה יש שני מלכודות: (א) המטריצות צפופות, ולכן קשה להגיע לרשתות גדולות, ו-(ב) בתדרים "אי-סדירים" הפתרון המתמטי אינו יחיד. את האחרון פותרים בניסוח Burton–Miller או בניסוח וריאציוני. הנורמל n חייב להצביע אל מחוץ לגוף, אל האוויר. נורמל הפוך הופך את הסימן של הלחץ.')
    heading(d, '4.3 קרקע קשיחה: שיטת הדמות', 2)
    para(d, 'כשהלוח עומד על קרקע קשיחה, הקרקע מחזירה את הקול ומכפילה את הלחץ בקירוב (עד +6 dB). משטח קשיח מקיים ∂p/∂n=0, ואת זה אפשר לספק בלי לדגם אותו: מוסיפים "תמונת ראי" של המקור והמשטח מתחת לקרקע, והשדה מעל הקרקע זהה לשדה של גוף סגור סימטרי. במחקר הקוד של Bempp-cl השתמש בשיטה זו.')
    fig(d, 'f08_bem', 15.5, 'BEM בחצי-מרחב חופשי (משמאל) ושיטת הדמות לקרקע קשיחה (מימין).')
    note(d, 'בקבצי LS-DYNA שהכנו הקרקע הקשיחה אינה ממומשת. ההפרש בין התוצאות של LS-DYNA ו-Bempp-cl ידרוש לכן תיקון של עד כ-6 dB בתדרים שבהם הקרקע משפיעה. אפשר לממש אותה ב-LS-DYNA על ידי שיקוף המבנה והעומס, אך זה לא נבדק.', 'הערה')

    heading(d, '5. אימות: איך יודעים שהמודל נכון', 1)
    para(d, 'סימולציה היא רק חישוב עד שמראים שהיא נכונה. חמש בדיקות מספריות עם סבילות שנקבעת לפני שמסתכלים בתוצאה:')
    T(d, 'בדיקות האימות ומה ביקשנו מהן', ['בדיקה', 'מה בודקים', 'ביצוע ב-LS-DYNA'], [
        ['תדרי לוח', 'מודים מול פתרון אנליטי (Mindlin) או מודל אחר', 'eigout מול CalculiX: 40.0 מול 40.1, 56.1 מול 56.2, 96.5 מול 96.5 Hz'],
        ['כדור פועם', 'BEM מול פתרון סגור', 'לא הורץ ב-LS-DYNA; הורץ ב-Bempp-cl בסטייה עד 0.08 dB'],
        ['קנה מידה', 'הכפלת העומס ב-2 מעלה את הרמה ב-6.02 dB', 'מכפילים את עקומת המשרעת ומשווים Press_dB'],
        ['התכנסות', 'חצי גודל רשת: שינוי קטן מהסבילות', 'מחדשים את הרשת ומריצים שוב'],
        ['עיבוד אותות', 'פסי אוקטבה על אות ידוע', 'סקריפט Python, 17 בדיקות עברו'],
    ], [3.0, 6.3, 6.5])
    para(d, 'עקרון חשוב: **משווים בין מודלים בלתי תלויים**. במחקר, כל מודל נוסף (CalculiX, Bempp-cl, קוד עצמאי, OpenRadioss) מצא או אישר טעות שלא נראתה במודל אחד. גם ההרצה הראשונה ב-LS-DYNA גילתה בעיה שנחשפה רק בהשוואה לתדרי CalculiX, כפי שמתואר בפרק 15.')

    # ============================================================ PART B
    d.add_page_break()
    heading(d, 'חלק ב: מעשה ב-LS-DYNA', 1)
    heading(d, '6. תהליך העבודה ומבנה קובץ הקלט', 1)
    para(d, 'LS-DYNA קורא קובץ טקסט (קובץ k) שמורכב מבלוקים. כל בלוק מתחיל במילת מפתח שמתחילה ב-`*`, ואחריה כרטיסים (cards): שורות של שדות שהמשמעות שלהם נקבעת לפי מיקומם. הערות מתחילות ב-`$`. הקובץ כולו מתחיל ב-`*KEYWORD` ומסתיים ב-`*END`. כדי לשמור סדר פיצלנו את המודל לשלושה קבצים שמחוברים ב-`*INCLUDE`.')
    fig(d, 'f10_anatomy', 14.0, 'מבנה קובץ הקלט: main.k כולל את mesh.k ואת loads.k, ומוסיף את בקרת הפתרן.')
    heading(d, '6.1 מוסכמות פורמט', 2)
    bullets(d, [
        '**פורמט קבוע:** רוב הכרטיסים הם 8 שדות ברוחב 10 תווים, מיושרים לימין. סטייה מהרוחב היא הטעות הנפוצה ביותר (ראו פרק 15).',
        '**חריגים:** `*NODE` הוא `I8` ואחריו שלוש קואורדינטות ברוחב 16; `*ELEMENT_SOLID` ו-`*ELEMENT_SHELL` הם שדות ברוחב 8; `*DEFINE_CURVE` שומר את נקודות העקום בשדות ברוחב 20.',
        '**כרטיסים מרובים:** רוב המילות מפתח מורכבות ממספר כרטיסים, והסדר קבוע. `*SECTION_DISCRETE` ו-`*FREQUENCY_DOMAIN_SSD` מדגימים זאת.',
        '**יחידות:** LS-DYNA לא מחזיק יחידות. אנחנו בחרנו SI עקבי: מטר, קילוגרם, שנייה, ניוטון, פסקל. הצפיפות בקילוגרם למטר מעוקב והלחץ ב-Pa.'])
    heading(d, '6.2 פקודת ההרצה', 2)
    code(d, '"C:\\Program Files\\ANSYS Inc\\v252\\ansys\\bin\\winx64\\lsdyna_dp.exe" i=main.k ncpu=4 memory=400m bem=1', title='שורת ההרצה (Windows)')
    T(d, 'פרמטרי שורת ההרצה', ['פרמטר', 'משמעות', 'הערה'], [
        ['lsdyna_dp.exe', 'דיוק כפול (double precision)', 'חובה לניתוח implicit. הגרסה lsdyna_sp.exe נכשלת (שגיאה 60022)'],
        ['i=main.k', 'קובץ הקלט', 'נתיב מלא או יחסי לתיקיית ההרצה'],
        ['ncpu=4', 'מספר ליבות', 'הרצה SMP; ב-BEM חלק מהשלבים מקביליים'],
        ['memory=400m', 'זיכרון במילים', 'אפשר גם בשורה `*KEYWORD MEMORY=400m` בקובץ עצמו'],
        ['bem=1', 'מפעיל את פותר ה-BEM האקוסטי', 'ללא זה: שגיאה 21275. הערך 1 הוא ההנחה שעבדה אצלנו'],
    ], [3.3, 5.0, 7.5])
    note(d, 'אם אתם מריצים דרך LS-Run, ערכו את תבנית הפקודה והוסיפו `bem=1` בסוף. בחרו את lsdyna_dp.exe בשדה הפתרן.')

    heading(d, '7. שלב 1: גיאומטריה ורשת', 1)
    para(d, 'הרשת של המחקר: לוח 1.0 על 1.0 מטר, עובי t, רשת הקסהדרלית אחידה בגודל 0.05 m. הלוח הקבור נקבר ב-0.4 m. בקובץ ה-mesh.k, הצמתים והאלמנטים נכתבים כך:', keep=True)
    code(d, grab('mesh.k', '*NODE', 4) + '\n...\n' + grab('mesh.k', '*ELEMENT_SOLID', 3), title='צמתים ואלמנטים מוצקים (קטע מ-mesh.k)')
    T(d, 'שדות *NODE ו-*ELEMENT_SOLID', ['מילת מפתח', 'שדות', 'הערות'], [
        ['*NODE', 'NID, X, Y, Z (TC, RC אופציונליים)', 'NID ברוחב 8, כל קואורדינטה ברוחב 16'],
        ['*ELEMENT_SOLID', 'EID, PID, N1…N8', 'שמונה צמתים של הקסהדרון, סדר נגד כיוון השעון'],
        ['*ELEMENT_SHELL', 'EID, PID, N1…N4', 'לפאנלי ה-BEM (פרק 12)'],
    ], [3.5, 6.0, 6.3])
    fig(d, 'f16_mesh', 15.0, 'פאנלי BEM ומיקרופונים במקרה t=100 mm קבור. הפאנלים מוגבלים לחלק שמעל קו הקרקע.')
    para(d, 'בחרנו את הצמתים כך שהצמתים של פאנלי ה-BEM הם גם צמתי הרשת המבנית. כך מהירות הצמתים המחושבת ב-SSD משמשת ישירות כתנאי השפה של ה-BEM, בלי אינטרפולציה.')

    heading(d, '8. שלב 2: חומר, חתך ו-part', 1)
    para(d, 'כל אלמנט שייך ל-`*PART`, שמקשר בין חתך (`*SECTION_*`) לחומר (`*MAT_*`). המבנה הוא `PID`, `SECID`, `MID`. הבטון הוא חומר אלסטי לינארי.')
    code(d, grab('mesh.k', '*SECTION_SOLID', 2) + '\n' + grab('mesh.k', '*PART', 2) + '\n' + grab('mesh.k', '*MAT_ELASTIC', 2), title='חתך מוצק, part וחומר הבטון (mesh.k)')
    T(d, 'כרטיסי החומר והחתך', ['מילת מפתח', 'שדות עיקריים', 'ערכי המחקר'], [
        ['*MAT_ELASTIC', 'MID, RO, E, PR', 'RO=2400 kg/m³, E=30 GPa, PR=0.2'],
        ['*SECTION_SOLID', 'SECID, ELFORM', 'ELFORM=18: hexa בן 8 צמתים עם מצבים לא תואמים לניתוח לינארי; נבדק מול C3D8I ב-CalculiX'],
        ['*PART', 'כותרת; PID, SECID, MID', 'part 1 = בטון'],
    ], [3.5, 5.0, 7.3])
    note(d, 'בלוח דק, אלמנט הקסהדרלי פשוט (ELFORM=1) נוקשה מדי בכפיפה (shear locking). לכן בחרנו באלמנט עם מצבים לא תואמים. השוואת התדרים העצמיים ל-CalculiX (אלמנט C3D8I) הראתה התאמה טובה.')

    heading(d, '9. שלב 3: אדמה וקרקע', 1)
    para(d, 'האדמה מוגדרת באלמנטים דיסקרטיים: קפיץ (`*MAT_SPRING_ELASTIC`) ובולם (`*MAT_DAMPER_VISCOUS`) שמחברים כל צומת של פני השטח הקבורים לצומת "קרקע" נעול. לכל זוג יש חומר, חתך ו-part משלו, והאלמנט עצמו הוא `*ELEMENT_DISCRETE`.')
    code(d, grab('mesh.k', '*MAT_SPRING_ELASTIC', 2) + '\n' + grab('mesh.k', '*MAT_DAMPER_VISCOUS', 2) + '\n' + grab('mesh.k', '*SECTION_DISCRETE', 4) + '\n' + grab('mesh.k', '*ELEMENT_DISCRETE', 4), title='קפיץ, בולם, חתך דיסקרטי ואלמנט דיסקרטי (mesh.k)')
    T(d, 'כרטיסי האדמה', ['מילת מפתח', 'שדות', 'הערות'], [
        ['*MAT_SPRING_ELASTIC', 'MID, K', 'K בניוטון למטר, לצומת'],
        ['*MAT_DAMPER_VISCOUS', 'MID, DC', 'DC בניוטון שנייה למטר'],
        ['*SECTION_DISCRETE', 'כרטיס 1: SECID, DRO, KD, V0, CL, FD. כרטיס 2: CDL, TDL', 'שני כרטיסים. DRO=0: שינוי אורך (תזוזה)'],
        ['*ELEMENT_DISCRETE', 'EID, PID, N1, N2, VID, S, PF, OFFSET', 'הכיוון נקבע לפי הקו בין N1 ל-N2'],
    ], [3.8, 6.8, 5.2])
    para(d, 'ארבעה פרטים שעלו לנו בניסיון:')
    bullets(d, [
        '**הכיוון** של האלמנט הדיסקרטי הוא קו הצמתים, ולכן כל קפיץ משמש כיוון אחד בלבד (x, y או z). מכאן 3 זוגות לכל צומת בנורמל ובשני כיווני החיכוך.',
        '**צומת הקרקע** ממוקם במרחק 1 m מהצומת של הלוח לאורך הכיוון, כדי לתת לקפיץ אורך מוגדר. הוא מקובע ב-`*BOUNDARY_SPC_SET`.',
        '**קיבוץ** חומרים עם ערך זהה לחומר אחד מקטין מאוד את מספר ה-part ואת קובץ הקלט (7 חומרי קפיץ ו-7 חומרי בולם במקרה t=100 mm קבור).',
        '**החתך הדיסקרטי** דורש כרטיס שני. בלעדיו הקורא "אוכל" את שורת ה-`*PART` הבאה כנתונים, ומתקבלות עשרות שגיאות נגזרות (פרק 15).'])
    code(d, '*BOUNDARY_SPC_SET\n$#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz\n         1         0         1         1         1         1         1         1', title='נעילת צמתי הקרקע (set 1)')

    heading(d, '10. שלב 4: ערכים עצמיים', 1)
    para(d, 'SSD מבוסס על מודים, ולכן קודם צריך לחשב אותם. בלוק הבקרה מורכב משלוש מילות מפתח:')
    code(d, grab('main.k', '*CONTROL_IMPLICIT_EIGENVALUE', 4) + '\n' + grab('main.k', '*CONTROL_IMPLICIT_GENERAL', 2) + '\n' + grab('main.k', '*CONTROL_IMPLICIT_SOLUTION', 2), title='בקרת הערכים העצמיים (main.k)')
    T(d, 'שדות עיקריים', ['שדה', 'משמעות', 'ערך המחקר'], [
        ['NEIG', 'מספר המודים לחישוב', '60'],
        ['IMFLAG (GENERAL)', 'מצב implicit', '1'],
        ['EIGMTH', 'שיטת פתרון הערכים העצמיים', '0 (ברירת מחדל)'],
        ['LFLAG/LFTEND, RFLAG/RHTEND', 'בחירת תחום תדרים במקום מספר מודים', 'לא בשימוש'],
    ], [4.5, 6.8, 4.5])
    para(d, '**כמה מודים?** הקריטריון הוא שהמודים מכסים לפחות את התדר העליון בניתוח, 1414 Hz בלוח שלנו. ב-CalculiX 16 מודים נמצאים מתחת ל-1414 Hz ושישים מגיעים עד 3909 Hz, כלומר 60 מספיקים. בדקו תמיד שהמוד האחרון ב-eigout מעל התדר העליון (עדיף כפליים).')
    heading(d, '10.1 בדיקת שפיות של eigout', 2)
    para(d, 'הקובץ eigout מכיל את הערכים העצמיים. שלוש בדיקות מיידיות: (א) האם המוד הראשון סביר? (ב) האם יש "גוש" של תדרים נמוכים צפופים שאינם פיזיקליים? (ג) האם התדר האחרון גבוה מספיק? בהרצה הראשונה שלנו נכשלנו בבדיקה (ב) ו-(ג), כפי שמראה האיור.')
    fig(d, 'f14_eigen', 13.0, 'הערכים העצמיים בהרצה הראשונה ב-LS-DYNA מול CalculiX. יש התאמה בחמישה מודים אמיתיים ראשונים (40.0, 56.1, 96.5, 119 ו-131 Hz בקירוב), אך שאר המודים מדומים, ו-60 המודים נגמרים ב-159 Hz בלבד.')

    heading(d, '11. שלב 5: עומס ו-*FREQUENCY_DOMAIN_SSD', 1)
    heading(d, '11.1 עקומות עומס', 2)
    para(d, 'בניגוד לניתוח בזמן, בתחום התדר העומס מוגדר על ידי שני עקומים לכל עומס: משרעת ופאזה כפונקציה של התדר. עקום הוא `*DEFINE_CURVE` עם נקודות (תדר, ערך). במחקר העומס הוא יחידה בכל התדרים, ולכן משרעת קבועה ופאזה אפס:')
    code(d, grab('loads.k', '*DEFINE_CURVE', 5, 0) + '\n...\n' + grab('loads.k', '*DEFINE_CURVE', 5, 1), title='עקום פאזה (lcid 200) ועקום משרעת לצומת (lcid 1000), loads.k')
    para(d, 'הכוח הכולל של 1 N מחולק בין 9 צמתי טבעת הקידוח. לכל צומת עקום משרעת משלו, שערכו הוא הכוח בצומת. סכום הכוחות מדויק (1.000000 N), והמומנט נבדק ב-verify_decks.py.')
    fig(d, 'f12_loads', 9.5, 'חלוקת הכוח הצירי על צמתי הרשת בטבעת הקידוח.')
    fig(d, 'f13_curves', 15.0, 'עקומי העומס. משמאל: מה שהגדרנו. מימין: איך נראה אותו כרטיס עם ספקטרום כוח תלוי תדר (המחשה).')
    heading(d, '11.2 הכרטיסים של *FREQUENCY_DOMAIN_SSD', 2)
    code(d, grab('main.k', '*FREQUENCY_DOMAIN_SSD', 12), title='בלוק ה-SSD (main.k)')
    fig(d, 'f11_cards', 15.5, 'ארבעת סוגי הכרטיסים של *FREQUENCY_DOMAIN_SSD כפי שהוגדרו במחקר. שדות ללא ערך נשארים ריקים.')
    T(d, 'שדות *FREQUENCY_DOMAIN_SSD', ['כרטיס', 'שדה', 'משמעות', 'ערך'], [
        ['1', 'MDMIN, MDMAX', 'טווח המודים לשימוש', '1 עד 60'],
        ['1', 'FNMIN, FNMAX', 'חלופה: טווח תדרי מודים', '0.0'],
        ['2', 'DAMPF', 'יחס בלימה קבוע ζ לכל המודים', '0.01'],
        ['2', 'LCDAM, LCTYP', 'בלימה תלוית תדר (עקום)', '0'],
        ['3', 'NOUT, NOTYP', 'קבוצת הצמתים/סגמנטים של פלט לצימוד ל-BEM', '1, 2 (סגמנט סט)'],
        ['7', 'NID, NTYP, DOF', 'צומת העומס, סוג (0 = צומת), כיוון', 'לפי הצומת'],
        ['7', 'VAD', 'סוג העירור. במחקר 0 (עומס כוח). בדוגמה 8.4 של Ansys VAD=3 מציין עירור בתאוצה צומתית; שאר הערכים במדריך', '0'],
        ['7', 'LC1, LC2', 'עקום משרעת, עקום פאזה', '1000+i, 200'],
    ], [1.6, 3.6, 7.6, 3.0])
    note(d, 'התדרים שבהם מחושב ה-SSD נקבעים על ידי בקשות הפלט: `*DATABASE_FREQUENCY_BINARY_D3SSD` ו-`*DATABASE_FREQUENCY_ASCII_…_SSD`. בכרטיס של D3SSD מגדירים fmin, fmax ומספר תדרים (nfreq). במחקר: 44.19 עד 1414.3 Hz, 1000 תדרים.')
    code(d, grab('main.k', '*DATABASE_FREQUENCY_BINARY_D3SSD', 5), title='בקשת פלט והגדרת התדרים (main.k)')

    heading(d, '12. שלב 6: קרינה אקוסטית עם *FREQUENCY_DOMAIN_ACOUSTIC_BEM', 1)
    para(d, 'בלוק ה-BEM דורש שלושה דברים: (א) משטח BEM, שמוגדר כקבוצת סגמנטים (`*SET_SEGMENT`) שמורכבת מפאנלי מעטפת (`*ELEMENT_SHELL`); (ב) נקודות שדה (`*SET_NODE_LIST`); (ג) כרטיסי המילה עצמה.')
    code(d, grab('mesh.k', '*ELEMENT_SHELL', 3) + '\n...\n' + grab('mesh.k', '*SET_SEGMENT', 4) + '\n...\n' + grab('mesh.k', '*SET_NODE_LIST', 4, 2), title='מעטפת BEM, סגמנט סט וקבוצת המיקרופונים (mesh.k)')
    code(d, grab('main.k', '*FREQUENCY_DOMAIN_ACOUSTIC_BEM', 10), title='בלוק ה-BEM (main.k)')
    T(d, 'שדות *FREQUENCY_DOMAIN_ACOUSTIC_BEM', ['כרטיס', 'שדה', 'משמעות', 'ערך'], [
        ['1', 'RO, C', 'צפיפות האוויר ומהירות הקול', '1.2, 343'],
        ['1', 'FMIN, FMAX, NFREQ', 'תחום ומספר תדרים', '44.19, 1414.3, 1000'],
        ['1', 'PREF', 'לחץ ייחוס ל-dB', '2.0E-5 Pa'],
        ['2', 'NSID_EXT, TYPE_EXT', 'מזהה סט נקודות שדה חיצוניות; סוג (1 = סט צמתים)', '2, 1'],
        ['2', 'FFT_WIN', 'חלון FFT לתוצאות בזמן', '4'],
        ['3', 'METHOD', 'שיטת האלגוריתם: 1 Kirchhoff, 2 variational indirect BEM', '2'],
        ['3', 'MAXIT, TOL_ITER', 'פתרון איטרטיבי (GMRES): מקסימום איטרציות וסבילות', '1000, 1e-6'],
        ['5', 'SSID, SSTYPE', 'סט הסגמנטים של משטח ה-BEM; סוג (2 = סגמנט סט)', '1, 2'],
        ['5', 'LC1, LC2', 'עקומי מהירות. ריקים אם מקור המהירות הוא SSD', '0'],
    ], [1.5, 4.2, 7.3, 2.8])
    para(d, 'הערה על הערכים: אישרנו את פירוש השדות מול דוגמאות Ansys 8.3, 8.4 ו-8.5 ומול ההרצה שרצה לסיום. אימות מלא של כל שדה מול המדריך של הגרסה שלכם מומלץ, ובעיקר METHOD ו-TYPE_EXT.')
    bullets(d, [
        '**כיוון הנורמל:** סדר הצמתים בכל סגמנט קובע את כיוון הנורמל, והוא חייב להצביע אל האוויר. בדקנו אותו בעבור כל פאנל לפי הסימון החיצוני, אך לא הוכחנו שה-BEM של LS-DYNA מפרש אותו כך. **נבדק לא סופית.**',
        '**מעטפת ה-BEM** היא חומר דמה (`*MAT_ELASTIC` עם E=1 Pa וצפיפות 1) כדי שיהיה לה `*PART`, והיא לא אמורה להוסיף קשיחות. אך לצמתי המעטפת היו דרגות סיבוב עם קשיחות כמעט אפס, שיצרו מודים מדומים (פרק 15). הפתרון הוא `*BOUNDARY_SPC_SET` שנועל את דרגות הסיבוב של צמתי המעטפת.',
        '**קרקע:** לא ממומשת. ראו פרק 4.3.'])
    code(d, grab('mesh.k', '*BOUNDARY_SPC_SET', 2, 1), title='נעילת דרגות סיבוב של צמתי המעטפת (mesh.k)')

    heading(d, '13. שלב 7: הרצה וניטור', 1)
    para(d, 'מתחילים את ההרצה מ-LS-Run או משורת פקודה. בזמן ההרצה LS-DYNA מדפיס לקובץ messag ולמסך. סימני חיים שרואים: אתחול, פתרון ערכים עצמיים, שלב SSD, ואז שלב ה-BEM שמדפיס שורה לכל תדר:')
    code(d, '  frequency  0.72582E+03 Iter      25  Residual  0.91121E-06\n  frequency  0.72444E+03 Iter      27  Residual  0.76110E-06', title='דוגמה לפלט שלב ה-BEM (הפתרן מתקדם מהתדר הגבוה לנמוך)')
    para(d, 'כל שורה היא תדר אחד, ומספר האיטרציות והשארית (residual) אומרים אם GMRES התכנס. שארית מתחת לסבילות (כאן 1e-6) היא סימן טוב.')
    T(d, 'זמני ריצה, t=100 mm קבור, 4 ליבות (BEM_time_report)', ['שלב', 'CPU [s]', 'הערה'], [
        ['בניית אלכסון (diagonal)', '35', ''],
        ['בניית מטריצה מחוץ לאלכסון', '303', 'השלב היקר'],
        ['פתרון GMRES', '135', '1000 תדרים'],
        ['אינטגרציה בנקודות שדה', '2', ''],
        ['סה"כ ריצה', '504', 'כ-8.4 דקות'],
    ], [6.0, 3.0, 6.8])
    para(d, 'בסיום, הסימן "N o r m a l   t e r m i n a t i o n" בסוף messag ובסוף d3hsp. היעדרו, גם כשנוצרו קבצי פלט, אומר שההרצה נכשלה באמצע.')

    heading(d, '14. שלב 8: קבצי הפלט ופענוח', 1)
    T(d, 'קבצי הפלט והשימוש בהם', ['קובץ', 'תוכן', 'איך פותחים'], [
        ['eigout', 'תדרים עצמיים, גורמי השתתפות ומסה אפקטיבית', 'עורך טקסט; שימושי לבדיקת שפיות'],
        ['d3eigv', 'צורות המודים (לתצוגה)', 'LS-PrePost: File, Open, LS-DYNA Binary Plot'],
        ['d3ssd', 'תזוזות ומאמצים בכל תדר', 'LS-PrePost, אותו אופן; בוחרים תדר ומשרעת/פאזה'],
        ['Press_Pa, Press_dB', 'לחץ בנקודות השדה: Pa ו-dB לפי PREF', 'טקסט בפורמט עקומים; XYPlot ב-LS-PrePost או Excel/Python'],
        ['bepres', 'לחץ ורמת קול על משטח ה-BEM', 'טקסט'],
        ['binout', 'פלט בינארי של ASCII', 'LS-PrePost: ASCII, Binout'],
        ['messag, d3hsp', 'לוג ההרצה וסיכום המודל', 'טקסט; כאן מחפשים שגיאות'],
    ], [3.0, 6.5, 6.3])
    fig(d, 'f15_press', 14.0, 'הקובץ Press_dB שנוצר בהרצה הראשונה. מיקרופון S נמצא במישור האמצע של הלוח ולכן ברמה נמוכה מאוד, כצפוי (דיפול).')
    heading(d, '14.1 מהקובץ לפסי אוקטבה', 2)
    para(d, 'Press_Pa הוא כבר פונקציית התמסורת לכוח של 1 N, ביחידות Pa/N. כדי לקבל רמה בפס אוקטבה צריך לשלב את ריבוע המשרעת על פני הפס, עם הנחה על ספקטרום הכוח. עם ספקטרום שטוח זהו הממוצע של |p|² בתוך גבולות הפס. הסקריפט `compare_lsdyna.py` עושה זאת ומשווה לתוצאות המחקר האחרות.')
    code(d, 'cd src\n"%LOCALAPPDATA%\\drill-lsdyna-venv\\Scripts\\python.exe" compare_lsdyna.py t10_bur ..\\lsdyna\\t10_bur', title='פענוח והשוואה ל-CalculiX ו-Bempp-cl')
    note(d, 'המיקרופונים F ו-R מקבלים לחץ זהה במחקר, כי הלוח סימטרי סביב מישור האמצע שלו והמיקרופונים נמצאים במרחק זהה משני צדיו. זו תכונה פיזיקלית ולא שגיאת מיפוי.')

    heading(d, '15. שגיאות אמיתיות ופתרונן', 1)
    para(d, 'הטבלה הבאה היא רישום של מה שקרה לנו בפועל, לפי סדר ההרצות. כל שגיאה נמצאה בקובץ d3hsp. חיפוש מהיר: `grep -n "Error" d3hsp`.')
    T(d, 'שגיאות ולקחים', ['קוד / הודעה', 'סיבה', 'פתרון'], [
        ['10459: item 2 of line is too long', 'שורת חומר עם פסיקים במקום שדות ברוחב 10', 'לכתוב בפורמט קבוע: `%10d%10.5G`'],
        ['10246: improperly formatted data, reading *SECTION card', 'חסר כרטיס שני ב-*SECTION_DISCRETE (CDL, TDL)', 'להוסיף שורה `0.0  0.0`'],
        ['10786: Non-numeric ID ... soil_k_11', 'שגיאה נגזרת: כותרת ה-*PART נקראה כנתונים', 'לתקן את השגיאה הקודמת'],
        ['10137: Multiply defined SECTION ID', 'שגיאה נגזרת מהקודמת', 'לתקן את השגיאה הקודמת'],
        ['10106 / 10375: undefined PID', 'ה-part של הבולם נפל בגלל חומר שגוי', 'לתקן את כרטיס החומר'],
        ['10246 ... reading *LOAD_NODE card', 'עומס `*LOAD_NODE_POINT` ברוחב שגוי; בנוסף SSD לא משתמש בו', 'להגדיר עומסים בכרטיס 7 של SSD עם עקומים'],
        ['10246 ... *FREQUENCY_DOMAIN_SSD, ACOUSTIC_BEM', 'סדר כרטיסים וקיצור רוחב שדות', 'להשתמש בפריסה מדוגמה 8.4 של Ansys'],
        ['21275: Command BEM= is missing', 'לא הוגדר bem בשורת ההרצה', 'להוסיף `bem=1`'],
        ['60022: Implicit is not supported in single precision', 'הרצה עם lsdyna_sp.exe', 'להשתמש ב-lsdyna_dp.exe'],
        ['תדרי eigout צפופים ונמוכים (12 Hz…)', 'צמתי מעטפת עם דרגות סיבוב לא קשיחות', 'לנעול dofrx, dofry, dofrz בצמתי המעטפת'],
    ], [4.8, 5.4, 5.6], size=9)
    fig(d, 'f17_flow', 14.5, 'טבלת הכרעה מהירה לפי תסמין בלוג.')
    note(d, 'שגיאה ראשונה היא כמעט תמיד האמיתית. עשרות שגיאות אחריה הן בדרך כלל נגזרות. תקנו את הראשונה והריצו שוב לפני שמנסים להבין את כולן.')
    note(d, 'הרצה שנגמרה ב-Normal termination אינה הוכחה לנכונות. ההרצה הראשונה שלנו הסתיימה בהצלחה, והתוצאות שלה עדיין היו שגויות בגלל המודים המדומים. תמיד בדקו את eigout לפני שמסתכלים בלחץ.', 'אזהרה')

    heading(d, '16. רשימת בדיקה לפני שסומכים על תוצאה', 1)
    T(d, 'רשימת בדיקה', ['בדיקה', 'מה מצפים'], [
        ['שורת הרצה', 'lsdyna_dp.exe, bem=1, ncpu ו-memory סבירים'],
        ['Normal termination', 'מופיע בסוף messag ו-d3hsp'],
        ['eigout', 'אין גוש תדרים דחוס נמוך; המוד האחרון גבוה מ-FMAX; הראשונים מתאימים למודל אחר'],
        ['סכום העומסים', 'הכוח הכולל 1 N והמומנט הנכון (verify_decks.py)'],
        ['נורמלי BEM', 'מצביעים לאוויר; לבדוק באמצעות מקרה פשוט כמו כדור'],
        ['קנה מידה', 'עומס כפול נותן +6.02 dB'],
        ['רשת', 'כלל 6 אלמנטים לאורך גל, ובדיקת רשת עדינה פי 2'],
        ['נקודת שדה על מישור אפס', 'מיקרופון במישור האמצע נותן רמה נמוכה מאוד: זה תקין'],
        ['קרקע ואדמה', 'לדעת מה מודל ומה לא; לציין בתוצאות'],
    ], [4.5, 11.3])

    heading(d, '17. יישום על המחקר והמסלול הבא', 1)
    para(d, 'במחקר הרצנו את כל המקרים בשני פתרנים עיקריים, CalculiX ו-Bempp-cl, ובדקנו אותם מול קוד עצמאי ו-OpenRadioss. ב-LS-DYNA הכנו ארבעה מקרים (t10_exp, t10_bur, t20_exp, t20_bur), שהרצנו עד כה רק את t10_bur. המסקנות ההנדסיות הן מהמחקר העיקרי ולא מ-LS-DYNA.')
    T(d, 'מצב ההשוואה ל-LS-DYNA', ['נושא', 'מצב'], [
        ['מודים אמיתיים', 'מתאימים ל-CalculiX: 40.0, 56.1, 96.5 Hz'],
        ['מודים מדומים (מעטפת BEM)', 'זוהו, ותוקנו בקובץ הקלט. תיקון עדיין לא הורץ'],
        ['רמות הלחץ', 'ההשוואה הראשונה הושפעה מהמודים המדומים; ההשוואה הנכונה עוד לא בוצעה'],
        ['קרקע קשיחה', 'לא ממומשת ב-LS-DYNA'],
        ['נורמלים', 'טרם אומתו מול פתרון ידוע'],
    ], [5.5, 10.3])
    para(d, 'הצעדים הבאים: הרצה מחדש של t10_bur עם הקובץ המתוקן; השוואת תדרים ורמות; מימוש קרקע באמצעות שיקוף; הרצת שלושת המקרים האחרים; ובדיקת מודל אדמה מוצק עם גבולות בולעים.')

    # ============================================================ appendices
    heading(d, 'נספח א: טבלת מילות מפתח', 1)
    T(d, 'מילות המפתח שבהן השתמשנו', ['מילת מפתח', 'תפקיד', 'קובץ'], [
        ['*KEYWORD, *TITLE, *END', 'מסגרת הקובץ וכותרת', 'main.k'],
        ['*INCLUDE', 'הכללת קובץ אחר', 'main.k'],
        ['*CONTROL_IMPLICIT_GENERAL', 'הפעלת ניתוח implicit', 'main.k'],
        ['*CONTROL_IMPLICIT_EIGENVALUE', 'חישוב ערכים עצמיים', 'main.k'],
        ['*CONTROL_IMPLICIT_SOLUTION', 'פרמטרי פתרון implicit', 'main.k'],
        ['*FREQUENCY_DOMAIN_SSD', 'תגובה הרמונית בסופרפוזיציית מודים', 'main.k'],
        ['*DATABASE_FREQUENCY_BINARY_D3SSD', 'תדרי הפלט של SSD (fmin, fmax, nfreq)', 'main.k'],
        ['*FREQUENCY_DOMAIN_ACOUSTIC_BEM', 'קרינה אקוסטית בשיטת BEM', 'main.k'],
        ['*NODE, *ELEMENT_SOLID, *ELEMENT_SHELL', 'רשת הלוח ופאנלי BEM', 'mesh.k'],
        ['*PART, *SECTION_SOLID, *SECTION_SHELL', 'חתכים ו-parts', 'mesh.k'],
        ['*MAT_ELASTIC', 'בטון ומעטפת דמה', 'mesh.k'],
        ['*MAT_SPRING_ELASTIC, *MAT_DAMPER_VISCOUS', 'קפיצי ובולמי אדמה', 'mesh.k'],
        ['*SECTION_DISCRETE, *ELEMENT_DISCRETE', 'אלמנטים דיסקרטיים לאדמה', 'mesh.k'],
        ['*SET_NODE_LIST, *SET_SEGMENT', 'קבוצות: קרקע, מיקרופונים, מעטפת BEM', 'mesh.k'],
        ['*BOUNDARY_SPC_SET', 'נעילת צמתי קרקע ודרגות סיבוב', 'mesh.k'],
        ['*DEFINE_CURVE', 'עקומי משרעת ופאזה של העומס', 'loads.k'],
    ], [6.5, 6.8, 2.5], size=9)
    para(d, 'מילות מפתח נוספות שמופיעות בדוגמאות Ansys, ולא השתמשנו בהן: `*FREQUENCY_DOMAIN_ACOUSTIC_BEM_PANEL_CONTRIBUTION` (תרומת כל פאנל), `*FREQUENCY_DOMAIN_ACOUSTIC_FRINGE_PLOT_SPHERE` (מפת קול על כדור), `*FREQUENCY_DOMAIN_RANDOM_VIBRATION` (עומס אקראי), `*FREQUENCY_DOMAIN_SSD_DIRECT` (פתרון ישיר בלי מודים), `*DATABASE_FREQUENCY_ASCII_NODOUT_SSD` (פלט צמתים ב-ASCII), `*MAT_ACOUSTIC` (חומר אקוסטי לשיטת FEM) ו-`*BOUNDARY_NON_REFLECTING` (גבול לא מחזיר).')

    heading(d, 'נספח ב: קובץ main.k המלא', 1)
    code(d, (DECK / 'main.k').read_text().rstrip().replace('\n$ ', '\n$ ')[:6500], size=7.5, title='main.k של המקרה t10_bur')

    heading(d, 'נספח ג: מושגים ויחידות', 1)
    T(d, 'מושגים עיקריים', ['English', 'עברית', 'הסבר קצר'], [
        ['eigenvalue / eigenmode', 'ערך עצמי / מוד', 'תדר וצורה שבהם מבנה רוטט חופשית'],
        ['SSD (steady-state dynamics)', 'תגובה הרמונית יציבה', 'מבנה שמעורר בתדר אחד ברציפות'],
        ['modal superposition', 'סופרפוזיציית מודים', 'סכום תרומות המודים'],
        ['damping ratio ζ', 'יחס בלימה', 'ζ=c/(2√(km))'],
        ['BEM', 'שיטת האלמנטים בגבול', 'פתרון על משטח בלבד'],
        ['field point', 'נקודת שדה', 'מיקום של מיקרופון'],
        ['coincidence frequency', 'תדר התלכדות', 'תדר שבו גל כפיפה = מהירות קול'],
        ['transfer function', 'פונקציית תמסורת', 'פלט ליחידת קלט'],
        ['octave band', 'פס אוקטבה', 'תחום תדרים fc/√2 עד fc·√2'],
        ['impedance', 'עכבה', 'כוח למהירות, ρc לגל'],
    ], [4.7, 4.0, 7.1], size=9.5)

    heading(d, 'מקורות', 1)
    for i, s in enumerate([
        'Ansys LS-DYNA, "Steady State Dynamic Analysis using Ansys LS-DYNA Software, Example", Synopsys/Ansys, 2025: https://lsdyna.ansys.com/wp-content/uploads/2025/12/SSDExample-001.pdf',
        'Ansys LS-DYNA Examples 8.3, 8.4, 8.5 (BEM acoustics of a plate, of a beam under SSD, of a simple car model): https://lsdyna.ansys.com/example-08-04/',
        'Ansys LS-DYNA Keyword User\'s Manual, Vol. I, בפרקי *FREQUENCY_DOMAIN, *CONTROL_IMPLICIT, *SECTION_DISCRETE ו-*DEFINE_CURVE.',
        'L. Cremer, M. Heckl, Structure-Borne Sound, 2nd ed., Springer, 1988.',
        'F. Fahy, P. Gardonio, Sound and Structural Vibration, 2nd ed., Academic Press, 2007.',
        'K. J. Bathe, Finite Element Procedures, Prentice Hall, 1996.',
        'A. J. Burton, G. F. Miller, Proc. R. Soc. Lond. A 323, 201–210, 1971.',
        'J. Lysmer, R. L. Kuhlemeyer, J. Eng. Mech. Div. ASCE 95, 859–877, 1969.',
        'T. Betcke, M. Scroggs, Bempp-cl, J. Open Source Softw. 6(59), 2879, 2021.',
    ], 1):
        para(d, f'[{i}] ' + s, size=9.5, space_after=2, align='left')
    out = OUT / 'LS-DYNA_manual_he.docx'
    d.save(out); print('saved', out)


if __name__ == '__main__':
    build()
