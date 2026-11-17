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

## Detail + presentation pass (task 3)
* No context city: renders use a dark gradient night sky + glossy studio ground disc (`render.py: night_world / ground / uplights / bloom`).
* Facade modules per sheet: M1 layered ribs + joints (`src/detail.py: rib, rib_joint`), M2 LED media screens with bezel / cyan edge (podium + fan flanks),
  M3 curtain-wall mullion grids + floor-by-floor warm interior glow, M3/B ring module (posts, glass balustrade, fascia band, brackets, underside light rings),
  M4 angled-cut chamfered armor panels with seams, M5 cyan strip channels, M6 stepped portal (jambs, fins, gable crown, canopy light grid, glazing grid).
* Materials M-01..M-05 (`ti_armor*`, `brushed`, `glass_curtain`, `screen_*`/`strip_*`, `struct_dark`) with render-time roughness noise + bump (`mats.py: surface_detail`).
* Presentation renders (Cycles, denoise, AgX, bloom; 1920×1080, elevations 1600×1800): `bash src/final_renders.sh final 128`
  → `renders/{hero_night,entrance_closeup,platform_closeup,atrium_interior,gallery_typical,elevation_front,elevation_side}_final.png`
* Web LOD: `model.glb` = full detail (LOD0); `model_lod1.glb` / `web/model_web.glb` drop the `D_*` facade-detail groups (panels, mullions).

## Metal exoskeleton pass (task 4, feedback "金属质感的外部构件")
* Real-depth metal members (`src/detail.py`): `exo_frame` (brushed-titanium box frame on every arm ridge, twin silver flanges forming a channel with the cyan M5 strip),
  `joint_plate` (node A, bolted plates at each station), `brace` (diagonal X bracing outside the glass), `buttress` (triangular base-corner fins, 0–40 m).
* M4 armor now covers the ridge half of every flank (large bevelled panels, 0.9 m deep, seams); glass only in the slot between armor and a gunmetal valley frame.
* Saucers / obs rings: silver rims, gunmetal underside cones + hubs, brushed struts; portal lintel / fins / gable in titanium + gunmetal.
* Materials: M-01 `ti_armor` light silver-grey (metallic 1, rough 0.30, anisotropic 0.55 render-only), M-02 `ti_armor2`/`ti_panel*` gunmetal, M-05 `struct_dark`.
* Lighting: HDRI-like night dome for reflection rays (bright cool horizon band, warm glow below), `metal_lights` rim/key area lights; camera still sees the dark sky.
* `python3 src/metal_sheet.py` → `compare/metal_vs_sheet.png` (sheet front view | model front elevation | hero).
