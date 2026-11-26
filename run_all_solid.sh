#!/bin/bash
# waits for the production queue (already running), then runs the sensitivity variants
cd "$(dirname "$0")"
while [ ! -f results/ccx_t20_bur_solid.npz ]; do sleep 30; done
bash run_solid_variants.sh
