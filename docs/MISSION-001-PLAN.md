# TrafficLab — running project record

## Authority and intent
The project charter governs. General-purpose, empirically calibrated microscopic traffic laboratory; Pinole is the first scenario, never a core assumption. Macro outcomes must eventually connect to vehicle-level causes. Accuracy takes priority over visual plausibility. Recovered design discussion confirms a rewarding, interactive sequence of small vertical slices.

## Mission 001: Make Pinole Move — implementation plan
Build a real OpenStreetMap I-80 network around Pinole, import it with SUMO netconvert, create seeded synthetic demand, run SUMO and expose its vehicle trajectories in an interactive browser viewer. A replay viewer is this milestone's presentation layer: all motion comes from SUMO, with reruns through the CLI. Live parameter intervention is deferred, not simulated in JavaScript.

Structure: `trafficlab/network.py` (OSM adapter/conversion), `demand.py` (routes/flows), `simulation.py` (SUMO output export), `__main__.py` (CLI), `scenarios/pinole/` (data/config/provenance), `viewer/` (presentation), `tests/` (integration checks).

Dependencies: Python 3.10+, eclipse-sumo/traci/sumolib 1.27.1. Browser viewer uses native Canvas and no external tiles or JavaScript libraries. OpenStreetMap is the geometry source; ODbL attribution retained. Synthetic demand and SUMO defaults are explicitly uncalibrated.

Acceptance: real sourced I-80 geometry with identifiable local context; connected routes in both directions; cars visibly moving; pause, time seek, speed control, pan/zoom and click inspection; vehicle speed/lane/position; repeatable seed and version provenance; trips complete without collisions/teleports; documented fresh install and run commands.

Risks: external map availability; incomplete lane/connection tags and netconvert inference; cropped boundary effects; package/platform availability; replay size and browser performance. Freeze source extract and record hash. Test connectivity, completed trips and repeatability. Never call technical verification empirical validation.

## Decisions
- SUMO is the physics engine; browser renders exported states, never invents dynamics.
- Scenario configuration separates geography from reusable modules.
- File boundaries are sufficient adapters for this slice; avoid premature service infrastructure.
- Pin versions, source hashes and seed. Preserve raw source and conversion settings.
- Historical replay, calibration, held-out validation, driver-population experiments and geographic generalization remain later milestones.

## Status
Implementation in progress. GitHub authenticated as lexluttrell; exposed connector supports editing repositories but lacks repository creation. No TrafficLab repository exists among returned repositories. No unrelated repository will be repurposed.

## Scientific status and limitations
No measured traffic observations or calibration. OSM geometry is mapped data, not a surveyed lane inventory; conversion may infer lane widths, connections and speed limits. All demand and driver parameters are synthetic/default assumptions. No counterfactual inference is justified. Finite corridor boundaries and through-only initial demand omit local origin/destination behavior.

## Next milestone and research questions
Next (not implemented here): historical PeMS observations and replay foundations. Resolve station coverage, quality flags, temporal alignment, demand identifiability and calibration/held-out day split before performance claims. Investigate ramp demand and lane inventory before corridor calibration.
