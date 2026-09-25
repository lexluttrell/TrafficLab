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
Mission 001 is complete and publicly runnable at https://lexluttrell.github.io/TrafficLab/. Source is maintained at https://github.com/lexluttrell/TrafficLab. The user enabled main /docs publication on 2026-09-25. Hosted browser playback and vehicle inspection have been verified. Historical transfer notes below describe resolved blockers. Mission 002 is now authorized; its importer and observations viewer are in progress, with real-data access blocked.

## Scientific status and limitations
No measured traffic observations or calibration. OSM geometry is mapped data, not a surveyed lane inventory; conversion may infer lane widths, connections and speed limits. All demand and driver parameters are synthetic/default assumptions. No counterfactual inference is justified. Finite corridor boundaries and through-only initial demand omit local origin/destination behavior.

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
