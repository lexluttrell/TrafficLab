# Mission 002 — Observe Pinole

## Why this comes next
Mission 001 established actual road geometry and vehicle-level simulation. Mission 002 establishes what the corridor's detector record actually says, before fitting the simulation to it. Historical observations are aggregate detector data, not recorded individual vehicle trajectories. Replaying a historical time window must never imply that PeMS identifies the actual drivers or their lane changes.

## Smallest vertical slice
Import one local-calendar day of District 4 PeMS station metadata plus five-minute station observations, select I-80 stations within the scenario extent, and inspect station-level speed, count, occupancy, missing intervals and reported percent observed in a browser. Keep measured/reported aggregates separate from the synthetic SUMO replay. No calibration or counterfactual claims in this mission.

## Architecture and files
- `trafficlab/data/pems.py`: source-specific schema adapter, bounded streaming import, numeric checks and date/time validation.
- Normalized versioned JSON contract: station locations and IDs, time-zone-aware UTC timestamps, original local timestamps, five-minute interval semantics, reported speed/flow/occupancy, quality fields, source hashes and mapping filters.
- `viewer/observations.html` and companion assets: standalone local-file observations viewer, visible status when no data are loaded. Publish the viewer through `/docs`; do not publish imported private/raw files by default.
- Tests use clearly labeled fabricated fixture rows only. Fixtures never appear as historical traffic on the public site.

## Sources and access
Official access guidance: https://dot.ca.gov/programs/traffic-operations/mpr/pems-source
PeMS portal: https://pems.dot.ca.gov/
Caltrans requires a free approved account for historical downloads; approval typically takes one to two business days. No account or authenticated download has been supplied. Mission 002 completion is blocked on authorized source files. The user has been notified through a one-time task. Do not request passwords in chat, bypass login, or substitute annual/typical-weekday aggregates for a specific day's history.

First files: District 4 Station Metadata snapshot effective on/before a selected traffic date, and that date's `station_5min` archive. Record the effective metadata date explicitly. Station mapping to a SUMO edge/direction will require review against the actual selected station set, especially HOV/mainline distinctions and boundary stations.

## Acceptance criteria
1. Actual Pinole/I-80 station IDs/locations and one actual date, preserving direction and station type.
2. Raw source hashes, metadata effective date, import date, timezone and field definitions retained.
3. Missing intervals remain gaps; zero counts remain valid observations; no forward-fill or silent imputation.
4. Preserve percent observed; flag partial/imputed, missing and invalid values. PeMS speed is a reported/estimated quantity, not guaranteed directly measured speed.
5. Repeated import of identical inputs yields identical normalized bytes. Reject conflicting duplicates and metadata from the future.
6. Interactive station selection, time inspection and clear distinction from synthetic vehicle simulation.
7. Real-data coverage/quality reviewed before declaring the mission complete.

## Risks and staging
Access is the immediate blocker. Schema must be checked against downloaded source files before production acceptance. Naive local timestamps around DST changes can be ambiguous; reject transition days initially rather than invent UTC offsets. Five-minute aggregates cannot uniquely identify demand, turning movements or individual driver behavior. Mainline-only data may not support ramp inference. Adjacent stations may require extending the observation window beyond the current simulation extent, which must be a documented choice. Data redistribution terms must be checked before committing observed data to the public repository.

Current status: build importer/viewer and tests while awaiting authorized data. This is preparation toward the real milestone, not a replacement for historical replay.
