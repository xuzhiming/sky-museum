#!/bin/bash
# usage: loop.sh TAG -> rebuild, render masks + ortho beauty, compare
cd "$(dirname "$0")"
TAG=$1
python3 build.py 2>&1 | grep -E "^tris|rror|built"
python3 render.py --views front_mask,right_mask,top_mask,back_mask,left_mask,section_mask --tag $TAG 2>&1 | grep -E "rror"
python3 render.py --views front,right,top,section --tag $TAG --samples ${2:-12} --scale 0.5 2>&1 | grep -E "rror"
python3 compare.py $TAG
