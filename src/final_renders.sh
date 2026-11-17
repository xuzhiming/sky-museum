#!/bin/bash
# presentation renders (clean backdrop, no context city): Cycles + denoise + AgX + bloom, 1920x1080 (elevations 1600x1800)
cd "$(dirname "$0")"
TAG=${1:-final}; S=${2:-128}
python3 render.py --views ${VIEWS:-hero,entrance,platform,atrium,gallery,elev_front,elev_side} --tag $TAG --samples $S --scale 1.0 2>&1 | grep -E "done|rror"
echo RENDERS_DONE
