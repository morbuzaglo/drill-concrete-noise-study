#!/bin/bash
# all four cases, production solid-soil model (Vs 200, eta_s 0.05, block 1.5 m beyond the slab, depth 2 m, grading 1.2 up to 0.2 m)
cd "$(dirname "$0")/src"
export PATH="$LOCALAPPDATA/drill-lsdyna-venv/Library/bin:$PATH"
PY="$LOCALAPPDATA/drill-lsdyna-venv/Scripts/python.exe"
for c in t10_exp t20_exp t10_bur t20_bur; do "$PY" run_solid_cases.py $c _solid > ../logs/solid_$c.log 2>&1; done
