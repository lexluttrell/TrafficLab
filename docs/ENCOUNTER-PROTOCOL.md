# Encounter study — protocol 0.1

Recorded 2026-09-27 before downloading the trajectory sample. Machine-readable criteria: `research/encounters/protocol.json`. This is an internal, versioned protocol, not an external preregistration.

## Immediate scope

Build a reproducible quality audit and an inspection viewer using a bounded real trajectory sample. No fitted driver parameters, effect estimates, causal conclusions, or validated simulation changes are part of this slice. Existing SUMO scenarios remain unchanged.

I-24 MOTION is the preferred long-observation source. Its data page returned HTTP 502 during access attempts on 2026-09-27; no I-24 trajectory archive has been acquired. Use the public FHWA NGSIM I-80 API as a development fallback: the first 300 seconds of the first recording, all available vehicles at native 0.1-second resolution. Query the first timestamp before specifying the exact interval. The later intervals are not inspected. NGSIM's single-day, approximately 500 m site cannot supply independent-day validation or establish present-day Bay Area behavior.

## Questions and event definitions

The eventual primary question is whether repeated discretionary lane-changing encounters are associated with a sustained change in subsequent following-gap choices, beyond direct physical reactions and changing traffic conditions. Sign and magnitude are unknown. Smooth-leader exposure is a later, separate study.

For this development slice, identify lane-label transitions with at least 2 seconds stable in both old and new lanes, limited to I-80 mainline lanes 1–6. Flag actors with at least two stable transitions within 30 seconds as **repeated lane-change candidates**. This is a screening rule, not an aggression label or proof of discretionary intent. Lane boundaries, ramps, route intent and video would require further review.

Associate a transition with the reported follower in the destination lane only after checking same-frame identity, lane and longitudinal ordering. Separate these directly affected followers from future nearby-witness cohorts. Direct cut-in events cannot by themselves isolate psychological influence. Enumerate all candidates and retain the exclusion funnel. Choose at most three examples by usable before/after coverage, then time and actor ID; do not choose examples because their response supports the hypothesis.

## Measurement and quality

- Freeze raw API responses, schema, query URLs, retrieval time and hashes. Record the protocol hash with the acquisition manifest. Check bounded-query row counts and pagination completeness.
- Namespace IDs by source, site and recording. Vehicle IDs can repeat between recordings. Require one unambiguous record per vehicle/time; count and collapse exact duplicates, quarantine conflicting keys. Never merge vehicles across recording periods.
- Convert feet to meters with exactly 0.3048. Coordinates identify the vehicle's front center. Net bumper gap is leader front position minus follower front position minus **leader length**. Source space headway is front-to-front and must not be mislabeled as bumper gap.
- Compute net time gap only when speed is at least 2 m/s, a same-frame leader is present in the same lane, and net gap is nonnegative. Missing leader information is a gap, not zero. Do not interpret observed net time gap as a desired-headway parameter.
- Preserve source speeds and positions. Flag discontinuities, invalid geometry, unavailable leaders, and disagreement between position-derived and reported speed. Raw acceleration and jerk are not trustworthy response measures without a separate reconstruction/smoothing sensitivity study.
- Replay native samples. Do not interpolate through missing observations. Lane width/road styling in the viewer are illustrative; source lateral and longitudinal positions drive vehicle placement.
- Report availability of 10 seconds and 30 seconds on each side for both actor and follower, contiguous observation and valid gap coverage. Long windows alone do not certify a usable causal comparison.

Thresholds are engineering screens for this version, not established scientific cutoffs. Any revision must be recorded; inspected data remain development data.

### Exploratory selection amendment 01 — after the first audit

The three highest-coverage examples selected by the original rule are single-change actors. Preserve those three and add one separately labeled supplemental example: an inspectable actor with an earlier stable mainline transition in the previous 30 seconds, ranked by the same coverage/time/ID rule. No response magnitude or sign enters selection. This post-audit addition is recorded in `research/encounters/selection-amendment-01.json`; the original protocol and its acquisition hash remain unchanged. Retrospective repeated-change counts can include a subsequent transition; the supplemental example specifically requires a preceding transition. None is treated as a confirmed weaving exposure for causal inference.

## Evidence gates after the prototype

1. Establish sufficient high-quality exposures and comparison opportunities; conduct power/precision planning with independent encounters and clustered uncertainty, not frame counts.
2. Audit a smaller same-source observed road segment: geometry, demand, boundaries, follower dynamics, lane changes and multi-vehicle disturbance propagation. Fit a conventional baseline before considering adaptation.
3. Specify matching/adjustment for pre-event behavior, leader changes, density, relative speed, ramps and common disturbances. Account for spillover into comparison vehicles. Assess pretrends, placebo events, missing-track selection and alternative thresholds. Trajectories cannot reveal whether a driver noticed an event or felt an emotion.
4. Fit a minimal context/history-dependent extension only if it adds explanatory value beyond ordinary physical reactions. Estimate heterogeneous responses and decay with uncertainty; allow null and opposite responses. Never double-count the braking response already generated by following dynamics.
5. Freeze the model, analysis code and acceptance tolerances before evaluating untouched recording days. Test individual encounters, free-running vehicle groups, and corridor outcomes. Repeat stochastic runs with paired scenario inputs. A model that fits historical observations is not automatically validated for behavioral interventions.
6. Audit transfer to I-80 conditions and expand the corridor. Preserve the PeMS development/validation split. Five-minute detector aggregates can constrain corridor speeds and flows but cannot validate short-lived psychological effects or fine braking waves.

Insufficient evidence means the adaptation layer remains experimental or absent. The larger simulator can proceed with an explicitly uncalibrated conventional baseline while evidence is gathered.

## References

- FHWA, [I-80 dataset description](https://www.fhwa.dot.gov/publications/research/operations/06137/).
- FHWA, [NGSIM public data API and field metadata](https://data.transportation.gov/api/views/8ect-6jqj.json).
- I-24 MOTION, [official data documentation](https://github.com/I24-MOTION/I24M_documentation).
- Long et al., [Bi-scale car-following model calibration](https://arxiv.org/abs/2312.09393).
- FHWA, [Microsimulation model calibration guidance](https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm).
