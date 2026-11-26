#!/bin/bash
# sensitivity / convergence variants of the solid-soil model (coarse impedance grid: 37 frequencies); run after run_solid_queue.sh
cd "$(dirname "$0")/src"
export PATH="$LOCALAPPDATA/drill-lsdyna-venv/Library/bin:$PATH"
PY="$LOCALAPPDATA/drill-lsdyna-venv/Scripts/python.exe"
run() { "$PY" run_solid_cases.py "$@" > ../logs/solid_$1$2.log 2>&1; }
run t10_exp _base_c 200 0.05 1.5 2.0 1.2 0.2 coarse
run t10_exp _big_c  200 0.05 2.2 2.5 1.2 0.2 coarse
run t10_exp _fine_c 200 0.05 1.5 2.0 1.15 0.15 coarse
run t10_bur _base_c 200 0.05 1.5 2.0 1.2 0.2 coarse
run t10_bur _big_c  200 0.05 2.2 2.5 1.2 0.2 coarse
run t10_bur _Vs100_c 100 0.05 1.5 2.0 1.2 0.2 coarse
run t10_bur _Vs400_c 400 0.05 1.5 2.0 1.2 0.2 coarse
