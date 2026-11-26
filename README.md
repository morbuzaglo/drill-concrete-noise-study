# Drill structure-borne noise: concrete thickness x partial burial (open-source study + prepared LS-DYNA decks)

Status: numerical demonstration study with documented assumptions. No physical validation. LS-DYNA decks: `t10_bur` ran to normal termination in Ansys LS-DYNA R14 (v252, double precision, `bem=1`); the other three decks are generated the same way but not yet run. LS-DYNA acoustic levels are NOT yet reconciled with the open-source results (see `lsdyna/run_evidence_t10_bur`).
Report (Hebrew): `report/drill_noise_report_he.docx` and `.pdf`.
Theory + practice manual for LS-DYNA SSD/BEM (Hebrew, SVG figures): `report/LS-DYNA_manual_he.docx` and `.pdf` (rebuild everything with `python src/build_manual.py`; it runs the figure scripts, builds the docx twice for the static table of contents, and exports the PDF through Word).

## Version B: the soil as a SOLID block (instead of springs)
Same slab, load, Bempp-cl acoustics and post-processing as version A; only the soil model changes. Version A (springs) is untouched.
- Model: graded hex mesh of slab + soil block (`src/solidmesh.py`), soil condensed to the interface (`src/soil_solid.py`, MKL PARDISO via `pypardiso`), modal slab coupled to the soil dynamic stiffness (`src/coupled.py`), Lysmer dampers on the outer faces, hysteretic soil damping, half model about the drill plane.
- Run (from `src/`, venv python, PATH must contain `%LOCALAPPDATA%\drill-lsdyna-venv\Libraryin`): `bash ../run_solid_queue.sh` (4 production cases, ~20 min each), `bash ../run_solid_variants.sh` (7 convergence/sensitivity runs, results not stored in git), then `python analyze_solid.py`, `python fig_soil_mesh.py imp`.
- Verification: `validate_solid.py <case>` (modal vs direct solve), `check_ccx_solid.py <case>` (CalculiX statics/modes on the same mesh), `footing_check.py` (rigid footing vs closed form).
- Reports (Hebrew): `report/drill_noise_report_solid_he.docx/.pdf` (`python make_report_solid.py`, then `python export_pdf.py drill_noise_report_solid_he`) and `report/LS-DYNA_manual_solid_he.docx/.pdf` (`python build_manual.py solid`). Both include a comparison with version A.
- LS-DYNA decks with solid soil: `lsdyna_solid/<case>/` (`python make_lsdyna_solid_decks.py`, static check `python verify_solid_decks.py`). PREPARED, NOT RUN. The `*FREQUENCY_DOMAIN_SSD_DIRECT` card layout is assumed identical to `*FREQUENCY_DOMAIN_SSD` and is not verified; hysteretic soil damping is not represented.
- Main caveats: far-field mesh (0.2 m) is too coarse above ~300 Hz; soil shear-wave speed (not measured) strongly changes the buried-slab result at 63-125 Hz (slab-on-soil resonance); axial load only.

## Stack
CalculiX 2.22 (structure, SSD) + Bempp-cl 0.4.2 (Burton-Miller, ground by image method). In-house FEM/BEM (`src/fem.py`, `src/bem.py`) and OpenRadioss are cross-checks only.
## Installation (Windows, no admin rights)
```
powershell -ExecutionPolicy Bypass -File setup\setup_windows.ps1 [-WithOpenRadioss]
```
Creates the venv `%LOCALAPPDATA%\drill-lsdyna-venv` from `requirements.txt` (pinned versions), downloads CalculiX 2.22 from dhondt.de (SHA-256 checked) into `%LOCALAPPDATA%\CalculiX`, and optionally OpenRadioss from its official GitHub release into `C:\OpenRadioss`. Binaries are fetched, not stored in this repository. Needs Python 3.12; MS Word only for the PDF export.
LS-DYNA (commercial) is not included: use your own installation.

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
LS-DYNA decks: card layouts follow Ansys example 8.4 (SSD + acoustic BEM). Run with the double-precision solver and `bem=1` (`lsdyna\<case>\run.bat`, or in LS-Run: solver `lsdyna_dp.exe`, command line extended with `bem=1`). Rigid ground is not implemented in them; panel normal direction unverified.

## סיכום קצר
הלוח הדק (100 מ"מ) קורן יותר מהעבה (200 מ"מ) ב-3 עד 13 dB בפסי 63-1000 Hz. קבורה חלקית מפחיתה קרינה ב-3 עד 11 dB מעל 250 Hz; מתחת לכך הסימן תלוי בקשיחות האדמה. לא בוצע תיקוף פיזי.
