# Mission 003 — Connect observations to moving traffic

## Purpose and visible slice
Run the real SUMO network with time-varying entry counts derived from 2026-09-24 PeMS observations. Provide an automatically loaded, shareable moving replay with vehicle inspection and station-level observed/simulated comparisons. Preserve Mission 001 and the historical inspector as separate pages. This is a diagnostic baseline, not a calibrated historical reconstruction.

## Scope and staging
1. Simulate 07:30–08:30 local source time, use 15 minutes as warm-up, and export the 08:00–08:10 moving window at two-second sampling. Simulate every vehicle; reduced display sampling is not reduced demand.
2. Use the eastbound 400865 and westbound 401084 counts at internal entry boundaries on their mapped mainline edges. Insert just downstream of these detectors, retaining quality percentages. Eastbound input is only 75% observed. Within-bin departure timing, vehicle population and departure speed are assumed. No observed speed curve is imposed.
3. Through-only baseline: no injected ramp demand or exits. Three off-ramp stations lack counts, so do not invent their flows. Show this omission in the viewer and quantify downstream mismatches. Follow-up work must include ramp topology and identifiable demand estimation before calibration claims.
4. Compare SUMO E1 loops against PeMS at mapped downstream mainline stations in the same five-minute bins. Exclude warm-up, input boundary stations, ambiguous matches and lane-count mismatches from headline diagnostics. Primary diagnostics use 100%-observed intervals only; retain other records for inspection. These are same-day diagnostic comparisons, not held-out validation.
5. Reserve the uploaded Sunday 2026-09-13 archive for future external checks; do not tune on it. A Sunday is not a substitute for a second comparable weekday validation set.

## Architecture
- `trafficlab/historical.py`: observation-driven through-demand, explicit scenario station bindings, SUMO run and reproducible provenance.
- `trafficlab/comparison.py`: lane aggregation and diagnostic metrics, separate from simulation.
- `scenarios/pinole/historical.json`: region-specific entry/control detector bindings and time window.
- Existing viewer gains time-based frame interpolation and optional comparison panel; export to a separate hosted page with its own replay bundle.
- Inputs: original frozen OSM/SUMO network and authorized normalized Sept 24 PeMS bundle. No new network source required. Dependencies remain pinned in requirements.txt.

## Evidence and technical risks
PeMS timestamp anchor: Table 4.1 (printed p.52), *Pilot Testing of SHRP 2 Reliability Data and Analytical Products: Southern California*, DOI 10.17226/22332, https://rosap.ntl.bts.gov/view/dot/3611/dot_3611_DS1.pdf, reproduces PeMS field specifications. It identifies interval-start timestamps. Source-local clock is used directly for this baseline; no UTC alignment claims are needed.

Speed aggregation: that table describes flow-weighted speed. Across 3,456 actual mainline records, the arithmetic flow-weighted aggregation of lane fields differs from the reported aggregate by 0.02624 mph mean absolute error (rounding), versus 1.43334 mph for the harmonic alternative. Use vehicle-count-weighted arithmetic SUMO loop speeds as a documented comparison approximation; this does not prove identical detector estimation pipelines.

SUMO E1 definition/output: https://sumo.dlr.de/docs/Simulation/Output/Induction_Loops_Detectors_(E1).html. Use completed crossing counts and lane-count-weighted speed, retain occupancy separately. SUMO lane-change crossings and real loop geometry can differ. Mainline mappings are spatial/topological model bindings, not field-certified detector placements. Metadata age and lane inventory remain caveats.

## Acceptance
- Real SUMO-generated cars respond to the changing five-minute entry counts; all intended counts, rounding, actually inserted vehicles and waiting backlog are reported.
- Same inputs/seed reproduce trajectories and detector comparisons. No negative/missing count becomes zero silently.
- Visible historical date/time, exact playback range, entry markers, provenance and assumptions.
- Click/pick/follow cars; inspect simulated versus reported flow/speed per station and bin. Display discrepancy, even if large.
- Automated checks cover time binning, units, weighted aggregation, missing/partial records, input exclusion and timeline sampling; browser checks verify the hosted artifacts' controls.
- Report collisions, teleports and unfinished trips. No calibration or counterfactual validity claim. Geographic code stays in scenario configuration.
