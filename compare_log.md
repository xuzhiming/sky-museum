# Compare log – 云巅博物馆 / Cyberpunk Sky Museum

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
