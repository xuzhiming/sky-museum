#!/bin/bash
cd "$(dirname "$0")"
python3 build.py 2>&1 | grep -E "built"
python3 render.py --views front_mask,right_mask,top_mask,back_mask,left_mask --tag final 2>&1 | grep -E "rror"
python3 render.py --views front,right,top,section --tag final --samples 32 --scale 1.0 2>&1 | grep -E "done|rror"
python3 compare.py final
python3 render.py --views hero,hero2,atrium,gallery,obs,cutaway --tag final --samples 64 --scale 1.0 2>&1 | grep -E "done|rror"
echo ALLDONE
