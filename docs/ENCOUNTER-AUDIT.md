# Encounter feasibility audit — September 27, 2026

[Open the encounter lab](encounters.html) · [Protocol](ENCOUNTER-PROTOCOL.md) · [Machine-readable audit](encounter-data/index.json)

## Finding

A bounded real sample supports an inspectable short-interaction prototype. It does **not** establish a weaving-induced behavioral effect, a causal mechanism, calibrated driver parameters, or transfer to the current I-80 corridor.

I-24 MOTION remains the preferred source for longer before/after observation and separate validation days. Both the search fetcher and a direct request to `https://i24motion.org/data` returned HTTP 502. No I-24 trajectories have been downloaded and no access request has been sent. The predeclared fallback is FHWA's public NGSIM I-80 source, a single 2005 eastbound Emeryville recording.

## Acquisition and quality

Retrieved the first 300 seconds present in the NGSIM I-80 API, `[1113433135300, 1113433435300)` in source milliseconds. Thirteen deterministically ordered, bounded pages contain **317,579 source rows**. The server count was checked before and after acquisition; all source-row IDs are unique. Raw response hashes, query URLs, source schema and the pre-acquisition protocol hash are recorded in `research/encounters/acquisition-manifest.json`.

| Check | Result |
|---|---:|
| Vehicles | 607 |
| Retained rows | 317,579 |
| Exact duplicate rows | 0 |
| Conflicting vehicle/time keys | 0 |
| Malformed rows | 0 |
| Within-track time discontinuities | 0 |
| Median duration observed in this bounded sample | 57.4 s |
| 90th percentile observed duration | 73.6 s |
| Maximum observed duration | 119.1 s |
| Samples with unavailable reported leader | 19,625 |
| Samples below the 2 m/s time-gap threshold, with usable geometry | 6,526 |
| Samples with negative computed bumper gap | 915 |
| Samples with position-derived/reported speed disagreement >5 m/s | 26 |
| Samples with leader lane mismatch | 9 |

These are sample-level screens, not sensor confidence estimates. Flags may overlap. A negative one-dimensional gap can arise during lane-transition geometry or from tracking/label errors; it is not proof of a collision. Such samples are excluded from gap/time-gap values. Zero discontinuities does not prove persistent identity or accurate positions. The median and maximum durations are censored by the five-minute crop and road boundaries, not estimates of driver response duration.

The API's earliest timestamp converts to 15:58:55.3 PDT while the FHWA description names the first interval 16:00–16:15. Absolute clock alignment remains unresolved; this prototype uses relative source time only. The coordinate-to-lane relationship and recording identity require additional audit before a same-road simulation is built. Do not fit current Bay Area behavior to this older sample without a transfer study.

## Candidate funnel

| Screen | Transitions remaining / counted |
|---|---:|
| All observed lane-label transitions | 307 |
| Outside mainline lanes 1–6 | 62 excluded |
| Insufficient stable dwell / discontinuous transition | 36 excluded |
| Stable adjacent mainline transitions | 209 |
| Reported destination-follower relationship unverified | 4 |
| Verified pair, continuous 10 s before and 10 s after | 132 |
| Verified pair, continuous 30 s before and 30 s after | 11 |
| Retrospective nearby-repeat candidates among 10 s pairs | 63 |
| An earlier transition already occurred within 30 s, among 10 s pairs | 32 |
| Unique actors contributing those 32 prior-repeat transitions | 25 |

Counts are transitions, not independent experiments. Actors, followers and observation windows can recur or overlap. The repeated-change screen does not establish discretionary intent, visibility to nearby drivers, or aggression. Ten-/thirty-second continuity is an inspection gate, not complete statistical eligibility: additional gap quality, comparison opportunities and confounder handling are required.

## What is published

The viewer contains three primary examples selected by maximal minimum actor/follower 30-second coverage, then timestamp and actor ID. They are actor/follower pairs 21/41, 50/66 and 31/45. All three happen to be single-change actors under the screening definition. An explicitly exploratory amendment adds the highest-ranked already-repeated-change example, 3355/36. Selection never uses response direction or magnitude. The original protocol hash and three examples are preserved.

The repeated-change example exposes a crucial distinction: although both focal tracks are continuous for ±30 seconds, the follower has **0/300 usable pre-event time-gap samples** and 151/300 after the event. The source does not provide a usable preceding-vehicle baseline before this transition. It therefore cannot support a before/after gap estimate. It is retained as an inspection example, visibly labeled with this failure, rather than silently replaced by a more persuasive-looking event. The first three examples have respectively 190/300, 259/300 and 201/300 usable pre-event samples. These counts are screening diagnostics, not independent sample sizes.

Each export contains native 0.1-second observations around the transition, nearby vehicles within 130 m longitudinally of the focal vehicle, reported speeds, reconstructed bumper gaps, quality flags and leader IDs. Source lateral positions are shown on an expanded schematic lateral scale; longitudinal distances use a consistent scale. Camera coverage cannot show what a driver actually saw. No missing trajectory frames are interpolated. No observed speed or gap trace is imposed on the simulator.

The source API's license object lists CC BY-SA 3.0; its Common Core metadata names CC BY-SA 4.0. Both declarations are preserved. Display subsets include source attribution, the API license link and a description of transformations. Original raw pages remain locally cached under ignored `runs/encounters/raw/`; the repository contains retrieval instructions, hashes and only the selected derived windows.

## Decision and next work

**Proceed with measurement and exposure validation; do not fit an adaptation model yet.** The strong reduction from 132 short-window pairs to 11 long-window pairs makes longer recordings a practical priority. This is evidence about this crop's suitability, not a general finding about all NGSIM data.

1. Restore official I-24 access and audit a bounded actual-trajectory recording. Virtual trajectories reconstructed from a speed field are unsuitable for individual response analysis. Assign development/validation days before examining behavior.
2. Review tracking identity, lane transitions and measurement reconstruction; compare raw and cleaned estimates without choosing cleaning parameters to favor an effect.
3. Separate direct cut-in responses from possible nearby-witness exposure. Establish same-context comparison opportunities, exposure spillover rules and effective independent sample size before estimating effects.
4. Build a measured conventional baseline on a small same-source road segment. Validate demand, geometry and boundaries before fitting behavioral parameters.
5. Only then assess a minimal history-dependent extension, held-out encounters, free-running groups, corridor outcomes and transfer to I-80. The September 17 and 23 PeMS validation patterns remain unopened.

## Reproduce

From the repository root, with Python 3.11+:

```sh
python scripts/fetch-encounter-sample.py
python -m trafficlab.data.encounters
python scripts/export-encounters.py
python -m unittest discover -s tests -p test_encounters.py -v
python -m http.server 8765 --directory docs
```

Open `http://localhost:8765/encounters.html`. Retrieval verifies raw page hashes on reuse and the server row count. Analysis checks the original protocol hash, time grid, row count and page hashes. Each encounter's uncompressed hash is verified by the browser before display. The selection amendment is separately hashed in the audit. External source changes may prevent byte-identical reacquisition; preserve the original cached pages for an exact rerun.

## Verification

Five unit checks cover exact unit conversion, front-center versus bumper gaps, correct leader length, missing/same-time/lane relationships, stopped/negative gaps, exact duplicates versus conflicting keys, pagination repetition, missing-frame coverage, stable transitions, and prior versus future repeat classification. These use explicitly fabricated fixtures and establish software behavior, not empirical validity.

Two complete extractions from the frozen real pages produced byte-identical results for all five published data files. Chromium checked data loading, native-time seeking, playback, event reset, selection/restart, source-to-display numerical agreement, supplemental labeling, desktop/390 px mobile layout, and rejection of a deliberately corrupted encounter bundle. No browser script errors were observed. Existing SUMO parameters, outputs, and PeMS split files are unchanged.
