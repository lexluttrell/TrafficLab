# Mission 006 — Test the merge assumption

[Open the experiment panel](https://lexluttrell.github.io/TrafficLab/ramps.html#robustness).

Before calibration, test whether the operational corridor depends narrowly on the assumed 150 m acceleration lanes. This is a six-case same-day sensitivity experiment, not a search for the best-fit lane length or a claim of field accuracy.

## Predeclared design

- Nominal acceleration-lane settings: 100, 150 and 200 m, applied to both previously blocked eastbound merges.
- Seeds: 42 and 43 at every length. Each changes departure times within source bins, exit assignments and engine randomness. Within a seed, all lengths retain exactly the same vehicle IDs and scheduled departure times.
- Fixed: Sept 24, 07:30–08:30 source counts; central exit assumptions; original Krauss driver parameters; entries, model boundaries and 15-minute warm-up exclusion.
- Completion check: 15 additional minutes with no new scheduled demand. Kept separate from the historical scoring window.
- Score mask: the same 18 fully observed station-bins at 401269 and 400660 in every case. No independent westbound score. Flow-balance stations stay excluded.

Nominal length is a netconvert setting, not a surveyed dimension. Actual generated lane lengths and network/configuration hashes are included in the result JSON. Network shape around each merge also changes during conversion. The experiment tests this construction procedure, not just an isolated scalar while every coordinate remains fixed.

## Results

The interactive table publishes all six cases. The selected detail view shows per-origin completion and 95th-percentile trip/stopped time. Trip times cover completed trips through the drain period; time spent waiting outside the model before insertion is not included in trip duration or SUMO in-network waiting time. Unfinished trips would be excluded from the percentiles, so completion accounting must be read alongside them.

The playback remains the existing 150 m / seed 42 run. Selecting a study case changes diagnostics only. No shorter/longer-lane trajectory is falsely presented as the current animation.

| Lane setting | Seed | Inserted by 08:30 | Completed after drain | Count WAPE | Speed MAE |
|---|---:|---:|---:|---:|---:|
| 100 m | 42 | 14,407 | 14,407 | 7.22% | 4.47 mph |
| 100 m | 43 | 14,407 | 14,407 | 8.02% | 3.97 mph |
| 150 m | 42 | 14,407 | 14,407 | 7.16% | 4.53 mph |
| 150 m | 43 | 14,407 | 14,407 | 7.92% | 4.01 mph |
| 200 m | 42 | 14,407 | 14,407 | 7.23% | 4.56 mph |
| 200 m | 43 | 14,407 | 14,407 | 7.98% | 3.99 mph |

All six cases insert and finish all 14,407 prescribed vehicles, with no collisions or teleports at any recorded step. Completion therefore does not depend on exactly 150 m within this tested 100–200 m range and two seeds. This is limited operational robustness, not geometry verification.

The regenerated 150 m / seed 42 case exactly matches the existing replay frames, detector comparisons and completion report.

Two seeds do not establish a statistical confidence interval. The results apply only to this demand window and the tested geometry/driver/boundary assumptions. Do not select a physical lane length by minimizing detector error; verify it with field or imagery evidence. Additional weekdays should be assigned training and validation roles before calibration; Sunday remains unused.

## Reproduce

Install the pinned requirements and run from the repository root:

```sh
python -m scripts.merge_sensitivity
python -m scripts.export_sensitivity
python -m unittest discover -s tests -p 'test_sensitivity.py' -v
python -m http.server 8765 --directory docs
```

Default execution runs all six cases sequentially. One initial 200 m / seed 42 attempt produced truncated engine XML and was rejected by parsing; it was rerun with the same settings, not replaced by another seed. `--seeds 42` and `--seeds 43` may run independently; every case has its own output directory. Generated networks, reviewed observations, engine outputs and summaries live in `runs/sensitivity/l<LENGTH>-s<SEED>/`. Frozen OSM and aggregate observations are already bundled. Public `merge-sensitivity.json` retains reports, actual generated lane lengths, source hashes, demand-schedule hashes, per-origin statistics and score membership.

Export refuses an incomplete six-case set, changed score masks, changed schedules across lengths within one seed, or inconsistent trip accounting. Collision and teleport checks inspect every recorded step, including drain time, rather than just the final step. Percentiles use linear interpolation between sorted observations. Source and behavior assumptions from [Mission 005](MISSION-005.md) still apply.

Two study-accounting tests pass. Browser checks passed for all six desktop row selections, active-state labels, per-origin details, a mobile-friendly case selector, width overflow and replay loading; no page errors. The panel was visually reviewed. The first mobile row-click test timed out; the final UI also provides a case dropdown outside the horizontally scrolling table.
