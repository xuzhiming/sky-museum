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

## Sheet front-view pass (task 5)
* `hood()` (`src/exterior.py`, `P.HOOD`): pyramid glass entrance hood over the central third of the base (half-width 60 m at z 0, apex 112 m),
  faceted to hug the facade (2.5 m proud of the arm-tip face, 0.6 m at its corners so the plan valleys / 8-lobe count stay intact),
  3.2 m titanium edge members + cyan edge lines, 9 diagonal brushed members, gunmetal transoms with amber lines, central spine,
  14 m walk-through opening with titanium frame; the old stepped portal jambs / gable / fins are replaced by it (glazing + doors + canopy kept, 0–24 m).
  Group `Hood` is in the collision lists (circulation, web walk).
* Contrast: plates are gunmetal (M-02, albedo ~0.25), silver M-01 only on frames/edges; darker navy/purple sky; weaker reflection dome, fill light
  and uplights; bloom lowered; amber interior coves ~1.7× brighter; `hood_glow()` warm hall lights + ring spot.
* Saucers: thicker discs (6.5 / 8 / 6.5 m), four underside light rings on the cone (amber + one cyan), warm rim glow, more visible glass railings.

## Entrance hall + gold ring, warm grade (task 6)
* `P.ENTRY_HALL`: multi-storey entrance hall behind the hood — slabs L2–L5 cut over x ±30 m from the facade back to y −116 m
  (void from the L1 floor to the L6 slab, 0–97.5 m); glass balustrades, top rails, cyan lines and amber edge glow on all new slab edges
  (`interior.hall_edge_rails`). The hall opens into the L1 lobby, which connects straight to the Ø80 atrium.
* Second gold ring (`interior.entry_ring`): Ø42 m at y −140, centre z 22.5 (bottom ≈1.5 m on a stepped plinth), facing the hood —
  the sheet's front-view ring. The Ø36 ring in the main atrium is kept (interior sheet). The podium tip face behind the hood is removed and the
  two flank faces under the hood are clear glass; doors moved into the hood opening (the old recessed portal glazing is gone).
* Circulation spec: arm-0 spaces on L2–L5 now reference the floor that remains behind the void (4, −59); walk route L1 detours around the ring plinth.
* Grade: AgX Punchy look, warm reflection dome, warm rim/key lights (one cool rim kept), 6 of 8 uplights warm, warmer metals
  (silver 0.80/0.76/0.70, warm gunmetal), amber coves/strips ~1.5× brighter, gold emission 0.6, ring key/back lights (`hood_glow`).
