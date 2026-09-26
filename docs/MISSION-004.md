# Mission 004 — Ramps and boundaries

[Open the ramp experiment](https://lexluttrell.github.io/TrafficLab/ramps-before.html).

Actual SUMO vehicles now enter five ramps and leave four exits. This is a reproducible demand/topology experiment, **not a calibrated historical reconstruction**. The original synthetic demo, observation viewer and Mission 003 replay remain available.

## What changed

The frozen OSM extract extends west to connect the Appian westbound on-ramp. Explicit bindings use ramp name, type, direction, lane inventory and passenger-vehicle graph connectivity; nearest metadata location alone is insufficient (two Appian records share coordinates). These are provisional model route bindings, not surveyed detector positions. The westbound model ends on edge 618988020 before the Richmond ramps. The eastbound entry is now station 400430: five lanes, 100% observed during the run. Westbound entry remains 401084, also fully observed.

Five ramps supply reported five-minute entry counts (407262, 420689, 407268, 407295, 407298). Exit 407261 supplies reported counts. Missing exits use declared hour-total flow balance:

| Exit | Balance during 07:30–08:30 | Central fraction |
|---|---|---|
| Appian EB 407263 | (5277 − 4030) / 5277 | 23.63% |
| Pinole Valley WB 407305 | (6400 − 5714) / 6400 | 10.72% |
| Appian WB 407296 | (5679 + 840 − 6056) / (5679 + 840) | 7.10% |

Balance assumes negligible storage change and ignores travel-time alignment. Some balance inputs are partly observed. Fractions are capped to [0, 0.8]; low/high cases multiply by 0.75 / 1.25 and cap at 0.95. These are scenario bounds, not uncertainty confidence intervals. Exit assignments are made to departure cohorts; actual exit passage occurs later. We do not fabricate missing ramp measurements or force measured speeds.

Stations 400865, 400301, 401230 and 401480 are explicitly excluded from scores because they informed demand. Only 401269 and 400660 supply independent, fully observed score bins: two eastbound stations × nine intervals after a 15-minute warm-up. No independent westbound headline score is available. Do not compare this score directly with Mission 003's different network, inputs and 36-bin mask.

## A failure worth seeing

The central case schedules 14,407 vehicles; 13,926 enter; 13,440 complete and 486 remain in the network. Another 481 never enter by cutoff. All mainline demand enters, but Appian EB loop 407262 admits only 62/224, and Pinole Valley EB ramp 407268 admits 73/392. These ramps queue at minor-priority merge connections. This diagnoses behavior of the present network and driver assumptions, **not real-world ramp queue lengths or proof of their cause**. Review acceleration lanes, merge priority and field geometry before tuning driver parameters. The model imposes no ramp metering or external arterial queues.

A preliminary `departLane=free` experiment blocked mainline insertion near an exit-only lane and was discarded. Route-aware `departLane=best` resolved that artifact; all four published cases use it. Mainline departure timestamps are identical across cases, generated independently per origin and interval. Ramp vehicle random trajectories can differ between scenarios because routing and interactions differ.

The central eastbound count WAPE is 10.74% versus 21.31% for the control; speed MAE is 4.37 versus 6.93 mph. Missing ramp traffic makes these incomplete diagnostics, not a successful calibration. The low-exit case leaves 477 uninserted (count WAPE 5.65%, speed MAE 5.05 mph); high-exit leaves 479 (17.75%, 3.83 mph). The differing best scores reinforce the need to assess both traffic delivery and speeds, rather than choose a case by one metric. The interactive page reports all four cases, demand delivery by origin, and the exit assumptions. Zero reported collisions or teleports does not prove geometric accuracy. Teleporting is disabled.

## Boundary review

At 08:00, westbound station 400301 reports 41.6 mph (100% observed), 401480 reports 44.3 mph (75%), 400929 reports 45 mph (80%), and farther west 400538 reports 25.7 mph (75%, ambiguous mapping). There is a slowdown to investigate beyond the original extent. Spatial variation, quality differences and one time slice cannot establish causality. The model imposes no downstream queue. Additional downstream coverage, field geometry checks and multi-day observations are needed before choosing a boundary mechanism.

## Reproduce

Install the pinned requirements, then run from the repository root:

```sh
python -m trafficlab.historical --scenario scenarios/pinole-ramps --observations scenarios/pinole-ramps/observations.json.gz --output runs/ramps/final-central
python -m trafficlab.historical --scenario scenarios/pinole-ramps --config scenarios/pinole-ramps/control.json --observations scenarios/pinole-ramps/observations.json.gz --output runs/ramps/final-control
python -m trafficlab.historical --scenario scenarios/pinole-ramps --config scenarios/pinole-ramps/low.json --observations scenarios/pinole-ramps/observations.json.gz --output runs/ramps/final-low
python -m trafficlab.historical --scenario scenarios/pinole-ramps --config scenarios/pinole-ramps/high.json --observations scenarios/pinole-ramps/observations.json.gz --output runs/ramps/final-high
python scripts/export-ramps.py
python -m unittest discover -s tests -p 'test_ramps.py' -v
python -m http.server 8765 --directory docs
```

Open `http://localhost:8765/ramps.html`. SUMO 1.27.1 / seed 42; one-hour run, 07:30–08:30 on September 24. The visible 08:00–08:10 window contains 301 samples at two-second spacing. Display interpolation is not a new simulated timestep. The browser does not run SUMO.

`ramps-study.json` records all four reports, detector records, exclusions, source hashes, parameters and exit audits. The bundled observation subset contains 28 stations × 288 records from the user-supplied District 4 archive, retaining missingness and observation-quality flags. Redundant raw lane/station strings are omitted. The original run's observation hash identifies the full normalized import; the compressed public aggregate file consequently has a different byte hash but identical fields used by demand and scoring. Frozen map source and network hashes are in scenario provenance. Original source archive and metadata hashes remain in the observation provenance.

No driver calibration, warm-up sensitivity analysis, held-out validation or causal inference was performed. September 13 Sunday remains unused. Next gate: resolve the two ramp merge/demand-delivery failures and review downstream boundaries; then add comparable weekdays and declare training/validation windows before calibration.

## Verification

Thirteen tests passed: eight source-import checks, three detector/count/quality checks, and two ramp checks including all four actual runs. They verify connected routes, unique demand IDs, exact trip accounting, shared mainline schedules, genuine ramp-origin completions and exits, no clipped targets, and score exclusions. Local Chromium passed replay loading, 600-second timeline, source clock, ramp-car selection, inspector/follow/zoom, detector exclusions, four-case table, insertion shortfall display, restart/end, mobile overflow and original-demo regression with no page errors. Full-page rendering was visually reviewed. These are implementation checks, not empirical validation.
