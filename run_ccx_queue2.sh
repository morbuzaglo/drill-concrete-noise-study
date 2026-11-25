#!/bin/bash
# Sensitivity runs on the dx=0.05 mesh: modal cutoff, soil stiffness variants. (ncols=1 axial uniform load)
cd "$(dirname "$0")/src"
export PATH="$LOCALAPPDATA/drill-lsdyna-venv/Library/bin:$PATH"
PY="$LOCALAPPDATA/drill-lsdyna-venv/Scripts/python.exe"
run() { [ -f ../results/ccx_$1$2.npz ] || $PY run_ccx_cases.py $1 0.05 $3 $2 $4 $5 > ../logs/ccx_$1$2.log 2>&1; }
for c in t10_exp t20_bur; do run $c _nm30 30 200 1.0; run $c _nm100 100 200 1.0; done
for c in t10_bur t20_bur t10_exp t20_exp; do run $c _Vs100 60 100 1.0; run $c _Vs400 60 400 1.0; done
for c in t10_bur t20_bur t10_exp t20_exp; do run $c _k05 60 200 0.5; run $c _k2 60 200 2.0; done
