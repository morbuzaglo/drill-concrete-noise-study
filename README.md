# Drill structure-borne noise: concrete thickness x partial burial (open-source study + prepared LS-DYNA decks)

Status: numerical demonstration study with documented assumptions. No physical validation. LS-DYNA decks are prepared and NOT run (no usable license).
Report (Hebrew): `report/drill_noise_report_he.docx` and `.pdf`.

## Stack
CalculiX 2.22 (structure, SSD) + Bempp-cl 0.4.2 (Burton-Miller, ground by image method). In-house FEM/BEM (`src/fem.py`, `src/bem.py`) and OpenRadioss are cross-checks only.
CalculiX: official Windows build from dhondt.de, unzipped to `%LOCALAPPDATA%\CalculiX` (ccx_static.exe). Python venv: `%LOCALAPPDATA%\drill-lsdyna-venv`
(`pip install numpy scipy matplotlib python-docx pandas pywin32 bempp-cl gmsh numba meshio pymupdf`).

## Reproduce (from `src/`, venv python)
1. Structure (4 cases, production dx=0.05): `bash ../run_ccx_queue.sh`  (sensitivity: `../run_ccx_queue2.sh`, `../run_ccx_queue3.sh`)
2. Acoustics (Bempp transfer vectors, ~2 h): `python run_bempp_T.py 3`
3. Cross-check BEM on CalculiX velocities: `python own_bem_all.py`, `python own_bem_O.py`, `python own_bem_dp01.py`
4. Analysis/figures: `python analyze.py bempp`, `python maps.py vib pres`, `python fig_geometry.py`, `python fig_protocol.py`
5. Verification: `verify_a_plate.py`, `verify_b_sphere.py`, `verify_c_scaling.py`, `verify_d_convergence.py`, `verify_e_dsp.py`, `verify_segments.py 0.025`, `crosscheck.py <case>`, `xcheck_free.py`, `or_xcheck.py 0.05` then `or_post.py`
6. LS-DYNA decks: `python make_lsdyna_decks.py` then `python verify_decks.py` (static check only)
7. Report: `python make_report.py` then `python export_pdf.py` (Word COM)

## Known limits
Bands 2-8 kHz unresolved (study covers 44.2-1414 Hz). Soil = impedance springs/dampers. Exposed soil surface not radiating. Stationary load only.
Microphone O (oblique) comes from the in-house BEM. OpenRadioss: resonance frequencies only (amplitude scale not validated).
LS-DYNA decks: FREQUENCY_DOMAIN_SSD / ACOUSTIC_BEM fields must be checked against the manual of your release; rigid ground is not implemented in them.

## סיכום קצר
הלוח הדק (100 מ"מ) קורן יותר מהעבה (200 מ"מ) ב-3 עד 13 dB בפסי 63-1000 Hz. קבורה חלקית מפחיתה קרינה ב-3 עד 11 dB מעל 250 Hz; מתחת לכך הסימן תלוי בקשיחות האדמה. לא בוצע תיקוף פיזי.
