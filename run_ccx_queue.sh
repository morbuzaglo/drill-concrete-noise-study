#!/bin/bash
# Production (dx=0.05) first, then mesh-convergence mesh. Each job writes results/ccx_<case>_dx<dx>.npz
cd "$(dirname "$0")/src"
export PATH="$LOCALAPPDATA/drill-lsdyna-venv/Library/bin:$PATH"
PY="$LOCALAPPDATA/drill-lsdyna-venv/Scripts/python.exe"
for dx in 0.05 0.0333333333333 0.025; do
  for c in t10_exp t10_bur t20_exp t20_bur; do
    [ -f ../results/ccx_${c}_dx${dx}.npz ] || $PY run_ccx_cases.py $c $dx 60 _dx${dx} > ../logs/ccx_${c}_dx${dx}.log 2>&1
  done
done
