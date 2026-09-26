# Mission 005 — Room to merge

[Open the current corridor](https://lexluttrell.github.io/TrafficLab/ramps.html) · [Original ramp queues](https://lexluttrell.github.io/TrafficLab/ramps-before.html)

## Explore flow

Use + / −, wheel or trackpad scrolling, or two-finger pinch to zoom. Wheel and pinch preserve the location beneath the gesture. Drag to pan; double-click to zoom in. Fit corridor resets the view. The location menu jumps to ramp boundaries and comparison detectors. Manual navigation releases vehicle-follow mode. With the map focused, use + / −, arrow keys, or 0 to fit.

Road color shows the arithmetic mean simulated speed of cars in each approximately 100 m road section, pooling lanes of the same directed edge. Ramps and opposing directions are separate. Red is below 20 mph, amber 20–40, yellow-green 40–55, and green 55+. Gray indicates no cars, not zero speed. Means use the current simulation sample, with no time smoothing or detector inference. Section boundaries reset at each network edge. New replay lanes include SUMO lengths; older replays fall back to polyline length for drawing bins. Displayed positions interpolate between recorded samples; speed and group membership use the preceding sample.

Cars default to **relative speed**: cyan means more than 5 mph faster than the other cars in that section, purple more than 5 mph slower, and white within ±5 mph. The selected vehicle is excluded from its peer mean. Fewer than two other cars means gray/insufficient peers. The inspector shows the numeric difference and peer count. The absolute-speed option restores mph bands; road coloring can be disabled independently. These are simulation layers, not live Google or PeMS traffic measurements.

## Why the ramps stopped

The imported model connected the Appian eastbound loop and Pinole Valley eastbound on-ramp directly into occupied mainline lanes under minor priority. It lacked acceleration lanes at those two merges. A new scenario rebuilds from the same frozen OSM with two explicitly assumed 150 m acceleration lanes. Ramp vehicles enter lane 0 without a crossing conflict; four through lanes feed lanes 1–4. Lane 0 ends, requiring an actual SUMO lane change to continue. Driver parameters, five-minute demand, exit fractions, seed and departure schedules are unchanged.

This follows SUMO's documented [motorway-ramp representation](https://sumo.dlr.de/docs/Simulation/Motorways.html#motorway-ramps) and [netconvert ramp options](https://sumo.dlr.de/docs/netconvert.html#ramp_guessing). The 150 m setting is a modeling assumption, not a measured length or a fitted optimum. Netconvert also recalculates geometry around the modified junctions. Do not interpret successful completion as field verification or calibration. The old bottleneck replay remains available for comparison.

## End-to-end result

| Sept 24, 07:30–08:30 | Original ramps | Assumed acceleration lanes |
|---|---:|---:|
| Scheduled | 14,407 | 14,407 |
| Inserted by 08:30 | 13,926 | 14,407 |
| Completed by 08:30 | 13,440 | 13,998 |
| Still in network at 08:30 | 486 | 409 |
| Not inserted by 08:30 | 481 | 0 |
| Eastbound count WAPE, same 18 bins | 10.74% | 7.16% |
| Eastbound speed MAE | 4.37 mph | 4.53 mph |

After demand stops at 08:30, a separately labeled 15-minute drain period checks completion. **All 14,407 trips complete**, with the last arrival at 08:32:51.4 source-local time. No cars remain in the network or outside waiting to insert; no collisions or teleports are reported. Every ramp-origin vehicle completes. Roads form an open entry-to-exit corridor; vehicles are not artificially recirculated. The visible replay remains 08:00–08:10 and the drain period never enters historical fit scores.

Count error improves, but speed error is slightly worse. This is a functioning modeled corridor, not proof of matching real traffic. Missing exits, partly observed balance inputs, single vehicle class, provisional station mapping, external boundaries and untested warm-up sensitivity remain limitations. Sunday remains unused. Next scientific gate: verify acceleration-lane geometry and downstream boundary behavior, then use additional weekdays with declared training and validation windows.

## Reproduce

Install the pinned requirements. The converted network and aggregate observations are bundled, so rebuilding geometry is optional:

```sh
python -m scripts.build_merge
python -m trafficlab.historical --scenario scenarios/pinole-merge --observations scenarios/pinole-merge/observations.json.gz --output runs/merge
python scripts/export-merge.py
python -m unittest discover -s tests -p 'test_merge.py' -v
node tests/test-flow-layer.cjs
python -m http.server 8765 --directory docs
```

The optional rebuild updates source-network hashes and station candidates. Original OSM provenance and attribution remain in `scenarios/pinole-ramps`; merge options and the assumed-geometry declaration are in `scenarios/pinole-merge/provenance.json`. SUMO 1.27.1, seed 42. The report records the demand-period cutoff separately from the completion drain. Network conversion warnings are retained; route and accounting checks do not certify geometry.

Sixteen Python tests passed, including original SUMO integration runs, plus JavaScript color tests and browser checks. Verification covers actual merge-lane connections, unchanged departure IDs/times, independent score mask, cutoff/drain separation, per-origin and all-trip completion, and zero reported collisions/teleports. Color checks exclude the selected car and separate directions, ramps and 100 m bins; sparse groups remain unknown. Local browser checks cover zoom anchoring, +/- buttons, wheel/follow interaction, location selection, keyboard pan/zoom, two-pointer pinch handlers, legends, road toggle, vehicle inspector, desktop/mobile layouts and earlier viewers. Native device pinch performance was not field-tested.
