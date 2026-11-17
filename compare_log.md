# Compare log – 云巅博物馆 / Cyberpunk Sky Museum

## Task 2: real drawing comparison (sheet_exterior.png / sheet_interior.png)

Method: `src/refmask.py` crops the 6 panels of the exterior sheet (front/back/left/right/top/longitudinal section), segments the
building from the navy background (linear bg fit through patches, threshold, close/fill/open), and maps each panel into the model's
3 px/m ortho frame with its own dimension lines (`ref/calib.json`: W/D 360 horizontally, ground→top 420 vertically; panels are not
uniformly scaled). `src/compare.py` compares with Blender mask renders (z ≥ 4 m for elevations): IoU, mean top-edge error, mean width-profile
error (5 m rows). Overlays: `compare/compare_<view>_<tag>.png`; final side-by-side: `compare/drawing_vs_model_final.png`.

IoU per view (front | back | left | right | top | section | mean):

| round | IoU | change before the round |
|---|---|---|
| s0 (= task-1 model) | 0.811 | 0.762 | 0.714 | 0.710 | 0.674 | 0.848 | **0.753** | baseline: brief numbers (setback at 48, Ro 180/168/136/96/44, rings at 320/360/400) |
| r2 | 0.911 | 0.942 | 0.914 | 0.910 | 0.784 | 0.827 | **0.882** | Ro(z) refit from the 4 elevation masks (21 stations, continuous taper, no 48 m setback), valley ratio, rear lean (yc to +22 m at 400 from side views), 3 saucer pods at drawn positions, twin needle spires, pentagon portal frame, screens z 12–78; interior restructured (below) |
| r3 | 0.912 | 0.942 | 0.914 | 0.910 | 0.820 | 0.827 | **0.888** | diagonal fan wings at the base (top view: 4 pointed cardinal arms + 4 fans) |
| r4 | 0.912 | 0.944 | 0.911 | 0.909 | 0.940 | 0.839 | **0.909** | `src/tune.py` coordinate descent (≈100 exterior-only evals, 2 passes, section weight 0.5): valley 0.94 @base, fans r×1.12 / ±24° / to z 76, pod P1 x −71, P3 x 84 R 38; second pass found no gain → plateau |
| r5 | (eval only) section 0.836–0.838 for all pod-z ±6 m variants | section-focused pass (section weight 1.0, pod heights): no improvement → stopped |
| final | 0.913 | 0.945 | 0.912 | 0.909 | 0.936 | 0.836 | **0.908** | fans capped r×1.10 (fans stay inside the 360 m elevation width); slim observation ring decks added at the labelled +320/+360/+400 |

Final dimension checks (`compare/scores_final.json`): 30/30 OK. Checks were updated for the drawn shape: the old "setback at 48",
"arm count by polar runs" and pod-contaminated width stations were measurement artifacts of the new silhouette (the drawn base
tapers continuously; 4 cardinal arms + 4 fans give 8 lobes; widths at 180/250 m hit the pods). Real issues fixed: rings at 320/360/400
missing (re-added), plan extent 390 m (fans capped → 358 m).

Sheet conflicts (logged, not resolvable from the drawing):
* Pod/platform labels say +320/+360/+400, but all four elevations draw three saucers at ≈180/265/290 m (section ≈208/287/305).
  Model keeps the drawn saucers (IoU) **and** slim ring decks at 320/360/400.
* Floor elevations: exterior table (L1 0–24, L2 24–48, L3–L10 48–180, L11–L20 180–320, L21–L27 320–360, L28–L29 360–400, L30 400–420)
  vs interior labels (+60 L2, +120 L3–5, +180 L6–10, +270 L11–20, +360 L21–27, +396 L28–29, +420 L30) vs "floor height 9–12 m".
  Model uses the exterior table (it matches the section's drawn floor bands); L21–L27 are therefore 5.7 m floors.
* The section panel is drawn wider than the elevations at the base (half-width ≈185–190 m vs 172–175 m) and its pods are 15–25 m
  higher → section IoU stays ≈0.84 without distorting the elevations.
* Top view fans reach r≈192–205 m in the drawing (beyond the 360 m dimension line); capped at the 360 m elevation envelope.

Interior corrections from sheet_interior: atrium Ø80 L1–L10 (0–180 m) closed by a conical soffit + core oculus at L11 (section A-A);
golden ring = thick vertical donut Ø36 standing on the atrium floor (centre z 21); atrium glass lifts L1↔L11 sky lobby; leaning central
glass core L11–L30 (4 HS lifts, stops L11/L21/L28/L29/L30); valley stair/lift cores only L1–L10 (upper plates too small), upper stairs
along the E/W arms in two vertical stacks (L11–L20, L21–L29); bridges removed; plan rings: corridor 7 m, halls 18–30 m, Ø80 void.

## Task 1 history (no sheets available; dimension-table checks only — superseded)

**Sheet IoU not computed this run.** The two design-sheet PNGs named in the task (`attachments/9e27fde0…png` exterior,
`attachments/1fa4d91c…png` interior) were **not present on the box** (empty attachments folder), so the sheet panels could not be
cropped / calibrated. The sheet branch of `src/compare.py` is implemented (panel crop → paper-colour segmentation → metres via the
panel's own dimension lines → 3 px/m grid → silhouette IoU + mean top-edge error + side-by-side/overlay `compare/compare_<view>_<tag>.png`)
and runs automatically once `ref/sheet_exterior.png` + `ref/calib.json` (template: `ref/calib.template.json`) exist: `bash src/loop.sh r5`.

What ran instead each round: orthographic mask renders (front/back/left/right/top, 3 px/m) are measured and checked against the
dimension table transcribed from the sheets (H 420, W/D 360, base segment 0-48, obs rings 320/360/400, spire to 420, 8 arms in top view)
plus the parameter profile `Ro(z)` at 6 heights. Scores: `compare/scores_<tag>.json`, sheet: `compare/comparison_sheet_<tag>.png`.

| round | result | change made before the next round |
|---|---|---|
| r1 | 13/18 OK. H 420.0, base W 361.0 (front), **D 364.3 (side, +4.3)**, base top 48.0, ring tops 321.3/361.3/401.3 (= deck + 1.3 m balustrade); **top-view arm count 31 / footprint r 229.5** | portal fins + canopy projected 4–14 m beyond the 360 m envelope → made flush / moved inside the 6 m recess; plaza light lines were in the building mask → moved to Ground group; arm-count metric switched to polar runs |
| r2 | 23/25 OK: D 361.0, arms 8, footprint r 181.5; widths @316/398 +20 m | (measurement) the probe heights hit the cantilever brackets under the ring discs → width probes moved to 120/180/250/308/340/385 m |
| r3 | 31/31 OK (all widths within +1.7…+2.3 m = rib + cyan strip depth outside the arm tips) | look-dev only: darker smoked glass, amber floor-edge lines, lighter strip LOD (−53k tris); silhouette unchanged |
| final | 31/31 OK, identical to r3 | final renders |

Residual / known deviations (to re-check against the sheet once it is available):
* Arm-tip width, valley depth (`VALLEY_RATIO`), and the taper stations inside each segment (`RO_PROFILE` 180→168 setback at 48, 136 @180, 96 @320, 44 @400) are estimates, not read off the drawing.
* Obs ring cantilevers (16/14/12 m) and the 400-410 glass crown + 410-420 spire split are assumptions.

## Task 3 – detail pass regression check
| tag | mean IoU | checks | note |
|---|---|---|---|
| d3 | 0.9088 | all OK | after rib depth 1.0 / joint size reduction (width tolerance 5 m: layered ribs stand ~2 m proud per side) |
| final | 0.9088 | all OK | podium/fan M2/M4/M5 detail; lobe counter changed from peak picking to circular runs > valley+5 m (fan plateaus carry detail ripples that broke `find_peaks`) |
| m4 | 0.9091 | all OK | metal exoskeleton frames (1.9 m deep), armor coverage, bracing, base buttresses |
| final (task 5) | see scores_final.json | | pyramid hood, gunmetal plates, thicker saucers |
