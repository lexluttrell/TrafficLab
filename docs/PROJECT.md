# TrafficLab — running project record

## Authority and intent
The project charter governs. General-purpose, empirically calibrated microscopic traffic laboratory; Pinole is the first scenario, never a core assumption. Macro outcomes must eventually connect to vehicle-level causes. Accuracy takes priority over visual plausibility. Recovered design discussion confirms a rewarding, interactive sequence of small vertical slices.

## Mission 001: Make Pinole Move — implementation plan
Build a real OpenStreetMap I-80 network around Pinole, import it with SUMO netconvert, create seeded synthetic demand, run SUMO and expose its vehicle trajectories in an interactive browser viewer. A replay viewer is this milestone's presentation layer: all motion comes from SUMO, with reruns through the CLI. Live parameter intervention is deferred, not simulated in JavaScript.

Structure: `trafficlab/network.py` (OSM adapter/conversion), `demand.py` (routes/flows), `simulation.py` (SUMO output export), `__main__.py` (CLI), `scenarios/pinole/` (data/config/provenance), `viewer/` (presentation), `tests/` (integration checks).

Dependencies: Python 3.11+, eclipse-sumo/traci/sumolib 1.27.1. Browser viewer uses native Canvas and no external tiles or JavaScript libraries. OpenStreetMap is the geometry source; ODbL attribution retained. Synthetic demand and SUMO defaults are explicitly uncalibrated.

Acceptance: real sourced I-80 geometry with identifiable local context; connected routes in both directions; cars visibly moving; pause, time seek, speed control, pan/zoom and click inspection; vehicle speed/lane/position; repeatable seed and version provenance; trips complete without collisions/teleports; documented fresh install and run commands.

Risks: external map availability; incomplete lane/connection tags and netconvert inference; cropped boundary effects; package/platform availability; replay size and browser performance. Freeze source extract and record hash. Test connectivity, completed trips and repeatability. Never call technical verification empirical validation.

## Decisions
- SUMO is the physics engine; browser renders exported states, never invents dynamics.
- Scenario configuration separates geography from reusable modules.
- File boundaries are sufficient adapters for this slice; avoid premature service infrastructure.
- Pin versions, source hashes and seed. Preserve raw source and conversion settings.
- Historical replay, calibration, held-out validation, driver-population experiments and geographic generalization remain later milestones.

## Status
Mission 001 is complete and publicly runnable at https://lexluttrell.github.io/TrafficLab/. Source is maintained at https://github.com/lexluttrell/TrafficLab. The user enabled main /docs publication on 2026-09-25. Hosted browser playback and vehicle inspection have been verified. Historical transfer notes below describe resolved blockers. Mission 002 has a runnable real-data historical inspection slice. Both source files are imported and reviewed; certified detector-to-edge mapping and timestamp anchoring remain unresolved. See the latest verification entry below.

## Scientific status and limitations
Real reported PeMS detector observations are now imported separately; no simulation calibration or held-out validation has been performed. OSM geometry is mapped data, not a surveyed lane inventory; conversion may infer lane widths, connections and speed limits. All demand and driver parameters are synthetic/default assumptions. No counterfactual inference is justified. Finite corridor boundaries and through-only initial demand omit local origin/destination behavior.

## Next milestone and research questions
Next (not implemented here): historical PeMS observations and replay foundations. Resolve station coverage, quality flags, temporal alignment, demand identifiability and calibration/held-out day split before performance claims. Investigate ramp demand and lane inventory before corridor calibration.

## Verification record — 2026-09-25
Implemented and locally runnable. Routes: 3,813.62 m and approximately 3,625 m, one per mainline direction; ramps retained without injected demand. The mapped corridor covers Appian Way and Pinole Valley Road context. Raw extract retrieval date and hashes are in `scenarios/pinole/provenance.json`; conversion warnings are preserved in `conversion.log`.

SUMO 1.27.1, seed 42: 600 inserted, 600 completed, 0 running/waiting at completion, 0 reported collisions, 0 reported teleports. Two independent runs had identical exported vehicle states. Every vehicle had multiple distinct recorded positions. These are technical checks, not calibration or held-out validation.

Standalone HTML opened in headless Chromium; zero page errors. Verified car click selection (car-0.12), inspector fields, pick-car, follow, zoom, fit, playback advance, end-time seek, restart, and no horizontal overflow at 390 px viewport width. Visually inspected screenshots of overview and selected-vehicle view. CLI server returned HTTP 200. Linux x86-64/Python 3.12 tested; other OS installs not exercised.

At initial delivery, the runnable slice was complete and repository creation was blocked. This was resolved by user-created repository, completed source transfer, and the successful Pages deployment recorded below. No later milestone has been implemented.

A standalone HTML with embedded actual trajectory data is generated for immediate offline interaction. It adds no alternative simulation model. Rerunning Python uses the real SUMO engine. Dependencies, frozen source, source code, instructions and local commit history accompany the handoff.

Additional limitations: one-second trajectory sampling with display interpolation; aggregate speed is the unweighted mean of active simulated vehicles, not a detector estimate; route-finding is currently a motorway-through-demand adapter. Context streets are display-only. Replay controls do not alter the simulation. No live TraCI control loop is claimed; that can be added behind the simulation adapter when an experiment requires it.

## GitHub and Pages handoff — 2026-09-25
The user created public `lexluttrell/TrafficLab` and explicitly requested GitHub Pages hosting. Source and a frozen replay are being transferred through the connected GitHub account. `docs/` contains the static Pages export; `scripts/export-pages.py` refreshes it after a simulation run. GitHub Pages serves precomputed SUMO trajectories and does not run SUMO server-side. No experiment or calibration scope is added.

The original three local commits remain available in the original release bundle. GitHub connector migration uses a new remote commit chain starting with the plan. Repository creation is resolved. Pages configuration is pending: connected tools expose file and commit operations, but not Pages settings or a collaborator-list audit. Public repository status and owner-admin connection permissions were verified. Do not claim that the collaborator list was audited or the site is live without evidence.

## Historical transfer recovery — 2026-09-25
Resumed the interrupted upload without rebuilding or changing Mission 001 scope. Raw OSM and hosted replay use lossless gzip for transfer/storage efficiency. The CLI handles the compressed source; the viewer decompresses replay data using the browser's DecompressionStream API. No geometry or simulation state was removed.

The repository snapshot contains the runnable Python project, frozen source/network, browser viewer, tests, provenance and a ready-to-publish `/docs` export. Initial local commits are retained in the previously delivered bundle; remote migration has its own commit identifiers. Repository creation is resolved. Current remaining deployment action: Settings → Pages → Deploy from a branch → main → /docs → Save. The connector cannot change Pages settings or list all collaborators, so neither site activation nor a full collaborator audit is claimed. Public visibility is retained at the user's request.

## Live deployment verification — 2026-09-25
GitHub Pages is active at https://lexluttrell.github.io/TrafficLab/, publishing main /docs. The public index, JavaScript and compressed trajectory data returned HTTP 200. A Chromium browser opened the actual public URL, decompressed the replay, scrubbed to 150 seconds and selected a vehicle; the inspector showed Krauss model details, with zero page errors. The live replay reports 600 completed trips. Mission 001 acceptance and requested public hosting are complete. Scientific status remains synthetic, uncalibrated and unsuitable for real-world counterfactual claims. Next milestone remains historical PeMS ingestion/replay foundations, pending a new work request.

## Mission 002 progress — 2026-09-25
User authorized progression after inspecting Mission 001. The plan is in `MISSION-002-PLAN.md`. Implemented a source-specific PeMS adapter and versioned observation contract, deterministic normalization, separate import receipt, source hashes, effective metadata date check, local-to-UTC timestamp handling, per-station coverage, missing-data gaps, preserved observed-percentage and invalid-value flags. Added a browser-local JSON inspection page with station selection, speed/count plots and timestamp inspection. It contains no fabricated public traffic data and does not publish user imports.

Access blocker: official historical PeMS downloads require a free approved account. No authorized District 4 archive has been supplied. Scheduled a one-time ChatGPT task notification at the user's request; phone delivery depends on notification settings. Real station coverage, source timestamp anchor, station-to-SUMO mapping and actual-date replay remain unverified. Mission 002 is not complete; no calibration or later milestone is started.

Schema reference: SANDAG/PeMS-Datasets at e6e125f65e45afdeceaebc4d6d0b5c92effa9e47. Eight importer tests passed using clearly fabricated fixtures, covering missing versus zero, partial/imputed flags, invalid occupancy, gzip inputs, duplicates, future metadata, DST transition rejection, station filtering and timestamp grid checks. Remaining acceptance requires genuine inputs and review of data usage/redistribution terms before public data publication.

Browser verification passed for the empty state, local JSON import, missing-interval display, preserved zero counts, partial-observation flags, repeated retina-canvas rendering and mobile width. No page errors. A fabricated QA file was used only in local testing and was not added to the repository or Pages export.


## Real-data review and local viewer — 2026-09-25
Input traffic date: 2026-09-24; metadata effective date: 2026-04-08 (169 days older). User supplied both original Clearinghouse files. The district archive reads through its gzip trailer, has 1,124,640 records, 3,905 station IDs, 288 timestamps, District 4 only, and no malformed field counts. Selected I-80 scenario coverage: 21 stations, 6,048 records, 288 rows per station, zero missing timestamp rows, zero conflicting or identical selected duplicates.

Source SHA-256:
- Observations: eda05caee29a85f92beab6bcfc7273170e481a983074d7b4b42ef9bd72a31fbe
- Metadata: e120c2a205a82c3b1b425ed0378c7bb06dfac86671e38c2ca551a66cfeb77ee8

Quality: 12 mainline stations have speed/count values at all 288 timestamps. Six mainline stations report 100% observed, five report 50–75%, and 400313 reports 0% throughout despite supplied speed/count values. All nine ramps lack speed values; six have counts, three (407263, 407296, 407305) have no flow or occupancy values. Missing ramp speed alone is not diagnosed as equipment failure. Preserved flags total 2,592 partial/imputed rows, 2,592 missing-speed rows, 864 missing-flow rows and 864 missing-occupancy rows (categories overlap).

Spatial review: all 12 mainline candidates lie within 7.5 m of direction-compatible motorway geometry. Station 401081 has a PeMS four-lane vs SUMO five-lane mismatch. Station 400313 has nearby alternative edges (2.0 vs 3.9 m). These remain provisional, and no `sumo_edge` has been certified. Ramps are shown at their reported locations with no invented edge mapping. Network hash accompanies every reviewed bundle. The reusable review module supports N/S/E/W headings; using a heading filter is an acknowledged approximation for curved networks.

Verification: eight importer regression tests pass. Two independent imports of the original inputs produced byte-identical normalized JSON; repeated spatial review likewise produced identical bytes. Chromium tested the actual 6,048-record standalone bundle and the public-viewer code with local file import: 21 station choices, 0%-observed warning, missing ramp fields, station-table selection, time inspection, lane-count flag, and mobile width all pass with zero page errors. Full-page visual review confirms map, quality table and four charts render. No claim of empirical simulation validation follows from these checks.

Deliverable: self-contained HTML with real observations and normalized JSON for local loading in the hosted inspector. Public repository includes source/viewer code and this review summary, not the raw or normalized archives. No redistribution permission has been inferred from successful account access.

Current milestone: Mission 002 historical inspection slice delivered; complete historical-to-simulation alignment is still pending. Remaining research: confirm source timestamp anchor/local clock convention; verify lane inventory and ramp topology against dated evidence; assess whether newer metadata exists; establish public redistribution terms. These do not prevent local inspection but must be resolved before fitting detector-aligned simulation results. Next planned milestone remains calibration and held-out validation, not started. One day's data is insufficient for a held-out day split.


## Shareable historical day — 2026-09-25
User explicitly requested a click-and-share hosted historical view. Published the normalized Pinole aggregate subset for 2026-09-24 as a compressed default bundle. Viewer loads it automatically and still accepts local imports. Preserved all station aggregate values, quality flags, metadata, provisional mapping and provenance; omitted unparsed raw per-lane strings from this display export. Original district archives remain uncommitted. Prior local-only delivery notes are superseded for this aggregate subset. User authorization to share is recorded; no broader PeMS redistribution license is claimed. Scientific caveats remain unchanged.

## Mission 003 baseline — 2026-09-25
User authorized the next phase: connect observations to moving SUMO vehicles. Implemented the staged plan in `MISSION-003-PLAN.md`. Separate historical page preserves Mission 001 and the observations inspector. PeMS timestamp anchoring is now documented as interval start via the reproduced PeMS specifications in Table 4.1, printed p.52, DOI 10.17226/22332 (https://rosap.ntl.bts.gov/view/dot/3611/dot_3611_DS1.pdf). Baseline uses source-local time directly; absolute UTC convention is still not independently established.

Run: 2026-09-24, 07:30–08:30; first 15 minutes excluded from metrics. Replay: 08:00–08:10, 301 frames sampled every 2 seconds, actual SUMO states. Entry boundaries: eastbound 400865 (75% observed) and westbound 401084 (100%). Source count per bin is preserved up to explicit integer rounding; within-bin departures are seeded uniform random times. No measured speeds are imposed. Original passenger-car/Krauss assumptions retained. No fitting was performed. Roads upstream of entry stations remain visible but do not receive generated vehicles.

10,430 vehicles scheduled and inserted; 10,108 completed before the cutoff; 322 still travelling; 0 waiting to enter; 0 collisions or teleports reported. Mean departure delay among completed trips: 0.0989 s. This is a finite observation window, not a run intended to drain all trips.

Diagnostic metrics: 36 fully observed downstream station-bins (4 stations × 9 post-warmup intervals). Count MAE 43.28 vehicles/5 min; count RMSE 48.46; count weighted absolute percentage error 10.13%. Speed MAE 13.00 mph, RMSE 16.45 mph, bias +9.30 mph. These are same-day baseline errors, not a calibrated validation score. At 400301 / 08:00, PeMS reports 41.6 mph and 537 vehicles, while the model produces 56.61 mph and 582. The missing slowdown is visible and not concealed by forcing a speed trace.

Station loops use projected positions on each lane, summed lane counts and vehicle-count-weighted arithmetic speed. Actual PeMS lane aggregation checked on 3,456 mainline records: mean absolute arithmetic aggregation discrepancy 0.02624 mph vs harmonic 1.43334 mph. Rounding explains the small arithmetic discrepancy; detector-estimator equivalence is not claimed. SUMO E1 crossing semantics: https://sumo.dlr.de/docs/Simulation/Output/Induction_Loops_Detectors_(E1).html. Occupancy remains recorded, not scored as proof of matching detector geometry.

Verification: three new accounting tests pass (aggregation and units, exclusion/missingness, seeded exact-count scheduling); eight importer tests still pass. A second full one-hour run with the same seed reproduced all exported trajectories, detector comparisons, reports and demand hash exactly. Entry and evaluation station sets are disjoint. Browser checks pass for historical autoload, 600-second playback on 2-second samples, source clock, vehicle pick/follow/zoom, per-station comparisons and quality exclusions, restart/end, mobile width, and the original Mission 001 viewer. Zero page errors; full-page layout visually inspected.

Status: Mission 003's first visible diagnostic baseline is runnable. Full historical reconstruction/calibration is NOT complete. Through-only demand deliberately omits ramp entries/exits; missing off-ramp observations make full demand identification unresolved. Input quality, provisional detector bindings, metadata age, default driver mix, downstream boundary conditions and untested warm-up sensitivity limit interpretation. Next work: verify ramp topology/lane inventory, build an explicit constrained demand-estimation step with uncertainty, then calibrate against declared training windows. The uploaded 2026-09-13 Sunday archive is reserved and has not been used for fitting or this baseline; obtain additional comparable weekdays for held-out validation. Do not draw counterfactual conclusions from this run.
