# 云巅博物馆 · Cyberpunk Sky Museum (modeling test)

Procedural Blender (bpy 5.3, Python only) model + Three.js viewer, following the cyber_louvre workflow.

| path | |
|---|---|
| `src/params.py` | parameter table (H 420, W/D 360, entrance 48, atrium Ø80, L1–L30 floor program, obs rings 320/360/400, spire 400–420) – all geometry derives from it |
| `src/exterior.py`, `src/interior.py`, `src/shapes.py`, `src/geom.py`, `src/mats.py`, `src/textures.py` | geometry / materials / procedural textures |
| `src/build.py` → `model.blend`, `tri_stats.json`, `circulation_spec.json` | build |
| `src/render.py`, `src/compare.py`, `src/loop.sh`, `compare_log.md`, `compare/` | ortho mask renders + comparison loop |
| `src/circulation.py` → `circulation_report.{md,json}` | reachability graph + BVH door probes + stair/escalator audit |
| `src/rebuild_web.sh` → `model.glb`, `web/model_web.glb`, `web/preview.html` | GLB export, gltf-transform (dedup, 1024 px, WebP, meshopt), self-contained viewer |
| `src/walk_test.py` → `renders/walk/` | headless Chrome walk/smoke test |
| `renders/*_final.png` | hero / entrance / atrium / L12 gallery / L28 deck / section cutaway; `renders/ortho/` elevations |

Rebuild everything: `bash src/final.sh && bash src/rebuild_web.sh && python3 src/circulation.py && python3 src/walk_test.py`

## Drawing comparison loop (task 2)
* `python3 src/refmask.py` – sheet panels → reference masks (`ref/calib.json`, outputs `ref/refmask_*.png`, `ref/panelm_*.png`)
* `bash src/mloop.sh TAG` – build + mask renders + IoU / top-edge / width-profile per view (`compare/scores_TAG.json`, overlays)
* `python3 src/tune.py compare/tune/tune3.json` – coordinate-descent tuning of exterior params (log `compare/tune/`)
* `bash src/final.sh` – final masks, ortho renders, checks, `compare/drawing_vs_model_final.png`, hero render
* history and sheet conflicts: `compare_log.md`
