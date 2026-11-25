#!/bin/bash
# soil/interface stiffness variants for the buried cases (parallel to queue 2)
cd "$(dirname "$0")/src"
export PATH="$LOCALAPPDATA/drill-lsdyna-venv/Library/bin:$PATH"
PY="$LOCALAPPDATA/drill-lsdyna-venv/Scripts/python.exe"
run() { [ -f ../results/ccx_$1$2.npz ] || $PY run_ccx_cases.py $1 0.05 $3 $2 $4 $5 > ../logs/ccx_$1$2.log 2>&1; }
for c in t10_bur t20_bur; do run $c _k05 60 200 0.5; run $c _k2 60 200 2.0; done
