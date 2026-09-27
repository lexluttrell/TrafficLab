# One car, paired traffic experiments

This is a playable, **uncalibrated model experiment**, not an estimate of real human responses. Controls load recorded SUMO runs. No vehicle dynamics are generated in JavaScript. The bounded nine-setting library makes experiments available on static GitHub Pages; a Python runner performs new engine runs locally.

## Protocol fixed before altered runs

Configuration: `scenarios/pinole-merge/driver-experiment.json`. Reuse the Mission 005 network and September 24 measured-count demand realization (seed 42). Keep all departure times, routes and population parameters fixed. Select the first eastbound full-through vehicle scheduled at or after 08:00: `o400430-1800-0`, scheduled at 1801.379 s after 07:30. Selection uses schedule and route, never response magnitude.

Cross target desired net time headway (`tau`) **1.0, 1.5, 2.0 s** with desired pace (`speedFactor`) **0.9, 1.0, 1.1**. Repeat all nine combinations with SUMO seeds **42, 43, 44**. No case or seed is chosen for the strongest result. Seed 42 is the preselected display run; all 27 results are published. Three seeds do not support a confidence interval or characterize model uncertainty.

Reference target: `tau=1`, `speedFactor=1`. Every case defines an identical target vehicle type except for tau, and explicitly assigns the target speed factor. The old replay assigned a random speed factor to this car, so it is not the paired reference. All other drivers retain their existing parameter distributions and Krauss/LC2013 models. Acceleration, braking, minimum gap, lane-change parameters and safety checks are unchanged. A desired pace is subject to traffic, road constraints and the vehicle maximum speed. A desired time gap is not a commanded actual gap.

The “Take it easy” preset selects 90% pace / 2 s; “In a hurry” selects 110% / 1 s. Names describe settings, not inferred psychological states. No emotional contagion, relaxation, retaliation or empirically identified weaving rule is implemented.

## Outcomes and checks

- Every trip's time includes SUMO `duration + departDelay`, so delayed insertion cannot masquerade as an improvement. Trips finish at model boundaries, not San Francisco.
- The nearby departure group is every **other** vehicle at entry 400430 scheduled in [1770, 1860) s. Membership is fixed before outcomes, includes all routes, and does not condition on actually following or meeting the target. It contains 106 vehicles. It is not a matched observational control group.
- Also report total trip-time difference for all 14,406 other scheduled vehicles, both directions and the rest of the hour. A vehicle-second total describes model-wide differences and must not be interpreted as a localized psychological effect.
- Require every scheduled trip to appear and complete after the no-new-demand drain, by 4500 s. Reject missing or unfinished trips; never silently calculate a completed-only cohort.
- Check every summary step for collisions and teleports, reconcile scheduled/inserted/ended/running/waiting, and preserve engine logs.
- Match canonical departure attributes and routes, fixed comparison membership and diagnostic-bin identity. Compare the entire sampled pre-entry traffic window, 1770 s through 1801 s, byte-for-byte within each seed. Identical seeds do not guarantee identical driver-level random shocks after trajectories diverge.
- Count target lane changes from SUMO lane-change output. Edge transitions and lane-index renumbering are not counted as lane changes.
- Recompute detector discrepancies against the same 18 eligible, fully observed eastbound station-bins for **every** run. Retain the individual observed/simulated records, denominator and excluded stations from the original study. No fitting or threshold that declares counterfactual validity is introduced.
- Source and network hashes, SUMO version, settings, commands and compressed replay hashes accompany the published library. The browser refuses a recording whose checksum disagrees with the index.

These PeMS comparisons use development data from the same day; they are not held-out validation. The baseline's speed and flow discrepancies remain visible. Matching aggregate traffic cannot validate individual responses, and an altered scenario is not expected to reproduce an unobserved real-world intervention. No reserved September 17/23 traffic patterns are opened, and no NGSIM or I-24 response parameter is fitted.

### Post-run diagnostic addendum

Before publication, an additional stochastic-divergence check was added across **all** cases: the 173 westbound vehicles at entry 401084 scheduled during the same [1770, 1860) s window. No case is removed or fitted using this check. Those trips cannot directly interact with the eastbound target on these routes. Their small nonzero paired differences demonstrate that shared seed alone does not isolate the target's physical effect from changes in random-number consumption. The evidence table publishes this check alongside nearby-group and all-other-trip differences. The nearby-group result must therefore be read as the paired model-run difference, including stochastic divergence, not a clean physical or psychological causal estimate. Isolating per-vehicle stochastic streams or adopting another controlled-noise experiment design is a next modeling gate.

## What the display measures

The movie covers 07:59:30–08:05:00 source-local time. Vehicle positions are recorded at 1 s; the published movie retains every second sample and interpolates 2 s positions for rendering. The target's metric samples retain 1 s resolution. Display interpolation is not an additional simulation engine. Source clocks and detector mappings retain the limitations of the original historical study.

FCD front-bumper positions and headings place vehicles on the actual SUMO geometry, including internal junction lanes. Street context is stationary. Follow, overview, pan, scroll/pinch zoom and a schematic driver camera are presentation controls. The reference outline is the same target in its paired run at the same clock time; it is not another interacting vehicle.

Gaps come from SUMO's leader output within a 200 m search. In SUMO 1.27.1, FCD `leaderGap` includes the minimum gap added back to the leader API's adjusted value, yielding net bumper-to-bumper space along the route. The highlighted follower is the closest reported vehicle whose leader is the target, with ID as a deterministic tie break. Its identity can change; we do not stitch different drivers into a single response estimate. Missing leaders/followers remain unavailable. Net time gap is distance divided by follower speed, unavailable below 2 m/s. Lines drawn between cars are visual connectors; route distance supplies the labels.

Road colors show simulated local mean speed in 100 m edge sections; they are not live traffic data or detector speeds. Ordinary car colors compare each car with at least two peers in that section: cyan above +5 mph, purple below −5 mph, pale within that band, gray with insufficient peers. Gold is the target, mint its current follower, and purple outline the reference. Presets and metrics remain inspectable independently of playback.

## Reproduce

Install the pinned `requirements.txt`, then from the repository root:

```sh
python -m trafficlab.driver_experiment --workers 3
python -m trafficlab.driver_experiment --case h10-p100 --seed 42 --output runs/drivers-repeat
python -m unittest tests.test_driver_experiment
```

The runner generates the original historical base through `trafficlab.historical` if absent and verifies its network, observation and demand hashes before use. `runs/drivers/` retains raw FCD, trip, lane-change, detector and summary files plus commands and logs. To refresh the hosted library and viewer after running:

```sh
python -m trafficlab.driver_experiment --export-only
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000/drivers.html`. GitHub Pages serves `main` / `docs`. A live arbitrary-parameter service and population controls are future work; this release deliberately exposes only the nine engine-run combinations.

Primary implementation references: [SUMO vehicle parameters](https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html), [randomness](https://sumo.dlr.de/docs/Simulation/Randomness.html), [lane-change output](https://sumo.dlr.de/docs/Simulation/Output/Lanechange.html), and [1.27.1 FCD source](https://github.com/eclipse-sumo/sumo/blob/v1_27_1/src/microsim/output/MSFCDExport.cpp).

## Next data gate

No additional PeMS day is needed for this slice. Longer I-24 trajectory data, after download access is verified, is the next acquisition priority. Audit tracking continuity, lane assignment, usable leader/follower gaps, pre-event history, exposure and comparison eligibility before fitting any response model. Preserve held-out recordings and days. Only after individual, platoon and corridor checks should a history-dependent behavior extension be used for real-world claims.
