#!/bin/bash
# final: build, masks, ortho beauty (6 views), sheet comparison, side-by-side sheet, hero + atrium renders
cd "$(dirname "$0")"
python3 build.py 2>&1 | grep -E "built"
python3 render.py --views front_mask,right_mask,top_mask,back_mask,left_mask,section_mask --tag final 2>&1 | grep -E "rror"
python3 render.py --views front,back,left,right,top,section --tag final --samples 24 --scale 0.5 2>&1 | grep -E "done|rror"
python3 compare.py final | grep -E "SHEET|XX"
python3 final_sheet.py final s0
python3 render.py --views hero --tag final --samples 64 --scale 1.0 2>&1 | grep -E "done|rror"
echo ALLDONE
