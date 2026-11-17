#!/bin/bash
# model.blend -> model.glb -> web/model_web.glb (dedup + 1024 + WebP + meshopt) -> web/preview.html
set -e
cd "$(dirname "$0")"
python3 export_glb.py 2>&1 | tail -1
G="npx --yes @gltf-transform/cli"
cd ..
$G dedup model_lod1.glb /tmp/sky_a.glb >/dev/null 2>&1
$G resize /tmp/sky_a.glb /tmp/sky_b.glb --width 1024 --height 1024 >/dev/null 2>&1
$G webp /tmp/sky_b.glb /tmp/sky_c.glb >/dev/null 2>&1
$G meshopt /tmp/sky_c.glb web/model_web.glb --level medium 2>&1 | tail -1
python3 src/make_preview.py
ls -la model.glb model_lod1.glb web/model_web.glb web/preview.html
