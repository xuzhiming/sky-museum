#!/bin/bash
# fast iteration: rebuild + mask renders + sheet comparison only
cd "$(dirname "$0")"
TAG=$1
python3 build.py 2>&1 | grep -E "^tris|rror|Trace" | cut -c1-80
python3 render.py --views front_mask,right_mask,top_mask,back_mask,left_mask,section_mask --tag $TAG 2>&1 | grep -E "rror"
python3 compare.py $TAG | grep SHEET
