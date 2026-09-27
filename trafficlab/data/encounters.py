"""Auditable NGSIM encounter inspection. This module does not estimate effects."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

FT = 0.3048
ROOT = Path(__file__).resolve().parents[2]


def normalize(raw, start):
    def number(key):
        value = float(raw[key])
        if not math.isfinite(value):
            raise ValueError(f"Nonfinite {key}")
        return value
    return dict(id=int(number("vehicle_id")), t=int(number("global_time")) - start,
                frame=int(number("frame_id")), x=number("local_x") * FT,
                y=number("local_y") * FT, length=number("v_length") * FT,
                width=number("v_width") * FT, speed=number("v_vel") * FT,
                lane=int(number("lane_id")), leader=int(number("preceding")),
                follower=int(number("following")), kind=int(number("v_class")),
                source_spacing=number("space_headway") * FT)


def deduplicate(rows, start):
    points, conflicts, counts, source_ids = {}, set(), Counter(), set()
    for raw in rows:
        counts["source_rows"] += 1
        source_id = raw.get("source_row_id")
        if source_id in source_ids:
            raise ValueError("Pagination repeated a source row ID")
        if source_id:
            source_ids.add(source_id)
        try:
            row = normalize(raw, start)
        except (ValueError, KeyError):
            counts["malformed_rows"] += 1
            continue
        key = (row["id"], row["t"])
        # Compare all source fields, not just the normalized subset.
        fingerprint = tuple(sorted((k, v) for k, v in raw.items() if k != "source_row_id"))
        if key in conflicts:
            counts["additional_conflict_rows"] += 1
        elif key in points:
            if points[key][1] == fingerprint:
                counts["exact_duplicate_rows"] += 1
            else:
                conflicts.add(key)
                del points[key]
                counts["conflicting_keys"] += 1
        else:
            points[key] = (row, fingerprint)
    counts["retained_rows"] = len(points)
    return {key: value[0] for key, value in points.items()}, counts


def measure_gap(row, lookup, minimum_speed=2.0):
    leader = lookup.get((row["leader"], row["t"])) if row["leader"] else None
    if leader is None:
        return None, None, "leader_unavailable"
    if leader["lane"] != row["lane"]:
        return None, None, "leader_lane_mismatch"
    gap = leader["y"] - row["y"] - leader["length"]
    if gap < 0:
        return None, None, "negative_net_gap"
    if row["speed"] < minimum_speed:
        return gap, None, "speed_below_time_gap_threshold"
    return gap, gap / row["speed"], None


def qualify(points, protocol):
    counts = Counter()
    tracks = defaultdict(list)
    for row in points.values():
        tracks[row["id"]].append(row)
    for rows in tracks.values():
        rows.sort(key=lambda r: r["t"])
        for i, row in enumerate(rows):
            flags = []
            if row["length"] <= 0 or row["width"] <= 0 or row["speed"] < 0:
                flags.append("invalid_dimensions_or_speed")
            if i and row["t"] - rows[i - 1]["t"] != 100:
                flags.append("track_discontinuity")
            before = points.get((row["id"], row["t"] - 500))
            after = points.get((row["id"], row["t"] + 500))
            derived = None
            if before and after and all((row["id"], t) in points for t in range(row["t"]-500, row["t"]+501, 100)):
                derived = after["y"] - before["y"]
                if abs(derived - row["speed"]) > protocol["quality_rules"]["position_speed_discrepancy_mps"]:
                    flags.append("position_speed_disagreement")
            gap, headway, gap_flag = measure_gap(row, points, protocol["quality_rules"]["time_gap_minimum_speed_mps"])
            if gap_flag:
                flags.append(gap_flag)
            if gap is not None:
                leader = points[row["leader"], row["t"]]
                if abs(leader["y"] - row["y"] - row["source_spacing"]) > 2:
                    flags.append("source_spacing_disagreement")
            row.update(gap=gap, time_gap=headway, derived_speed=derived, flags=flags,
                       gap_usable=headway is not None and not flags)
            counts.update(flags)
    return tracks, counts


def coverage(track, event_time, half_seconds, points):
    start, end = event_time - round(half_seconds*1000), event_time + round(half_seconds*1000)
    expected = round(half_seconds*20) + 1
    selected = [points.get((track, t)) for t in range(start, end+1, 100)]
    present = [row for row in selected if row]
    return {"seconds_each_side": half_seconds, "expected_samples": expected,
            "present_samples": len(present), "continuous": len(present) == expected,
            "usable_time_gap_samples": sum(row["gap_usable"] for row in present)}


def find_events(tracks, points, protocol):
    rules = protocol["candidate_rules"]
    dwell = round(rules["lane_dwell_seconds"] * 10)
    lanes = set(rules["mainline_lanes"])
    counts = Counter()
    events = []
    for vehicle, rows in tracks.items():
        changes = []
        for i in range(1, len(rows)):
            row, previous = rows[i], rows[i-1]
            if row["lane"] == previous["lane"]:
                continue
            counts["raw_lane_label_transitions"] += 1
            if row["lane"] not in lanes or previous["lane"] not in lanes:
                counts["non_mainline_transitions"] += 1
                continue
            if abs(row["lane"] - previous["lane"]) != 1:
                counts["non_adjacent_lane_jumps"] += 1
                continue
            old, new = rows[max(0, i-dwell):i], rows[i:i+dwell+1]
            if (len(old) != dwell or len(new) != dwell+1 or
                any(r["lane"] != previous["lane"] for r in old) or
                any(r["lane"] != row["lane"] for r in new) or
                any(b["t"]-a["t"] != 100 for a,b in zip(old+new, (old+new)[1:]))):
                counts["unstable_or_discontinuous_transitions"] += 1
                continue
            event = dict(actor=vehicle, t=row["t"], old_lane=previous["lane"], new_lane=row["lane"], follower=row["follower"])
            changes.append(event)
        for event in changes:
            counts["stable_mainline_transitions"] += 1
            event["repeated_candidate"] = any(other is not event and abs(other["t"]-event["t"]) <= rules["repeated_changes_within_seconds"]*1000 for other in changes)
            event["prior_repeat"] = any(0 < event["t"]-other["t"] <= rules["repeated_changes_within_seconds"]*1000 for other in changes)
            event["nearby_actor_changes_s"] = [(other["t"]-event["t"])/1000 for other in changes if abs(other["t"]-event["t"]) <= 30000]
            if event["repeated_candidate"]:
                counts["transitions_with_nearby_repeat"] += 1
            follower = points.get((event["follower"], event["t"]))
            actor = points[event["actor"], event["t"]]
            valid_pair = (follower is not None and follower["lane"] == event["new_lane"] and follower["leader"] == event["actor"] and follower["y"] < actor["y"] and follower["gap"] is not None)
            event["follower_relation_verified"] = valid_pair
            if not valid_pair:
                counts["follower_relation_unverified"] += 1
            event["coverage"] = {f"{name}_{seconds}s": coverage(event[name],event["t"],seconds,points) for name in ("actor","follower") for seconds in (10,30)}
            event["inspectable"] = valid_pair and all(event["coverage"][f"{name}_10s"]["continuous"] for name in ("actor","follower"))
            if event["inspectable"]:
                counts["inspectable_10s_pairs"] += 1
                if event["repeated_candidate"]:
                    counts["inspectable_repeated_10s_pairs"] += 1
                if event["prior_repeat"]:
                    counts["inspectable_prior_repeat_10s_pairs"] += 1
                if all(event["coverage"][f"{name}_30s"]["continuous"] for name in ("actor","follower")):
                    counts["continuous_30s_pairs"] += 1
            events.append(event)
    return sorted(events,key=lambda e:(e["t"],e["actor"])), counts


def quantiles(values):
    values = sorted(values)
    if not values:
        return {}
    return {"min":values[0],"median":median(values),"p90":values[round((len(values)-1)*.9)],"max":values[-1]}


def load_pages(directory, manifest):
    for item in manifest["files"]:
        body = gzip.decompress((directory/item["file"]).read_bytes())
        if hashlib.sha256(body).hexdigest() != item["sha256_uncompressed"]:
            raise ValueError("Raw source hash mismatch")
        rows = json.loads(body)
        if len(rows) != item["rows"]:
            raise ValueError("Page row count mismatch")
        yield from rows


def export_encounter(event, points, frames, directory, index):
    start, end = max(0,event["t"]-30000), event["t"]+30000
    packed_frames, series = [], []
    for t in range(start,end+1,100):
        actor, follower = points.get((event["actor"],t)), points.get((event["follower"],t))
        focus = follower or actor
        cars = []
        if focus:
            cars = [[r["id"],round(r["x"],3),round(r["y"],3),round(r["length"],3),round(r["width"],3),round(r["speed"],3),r["lane"],r["leader"],bool(r["flags"])] for r in frames.get(t,[]) if abs(r["y"]-focus["y"]) <= 130 or r["id"] in (event["actor"],event["follower"])]
        packed_frames.append([round((t-event["t"])/1000,1),cars])
        series.append(dict(t=round((t-event["t"])/1000,1),actor_speed=actor["speed"] if actor else None,
                           follower_speed=follower["speed"] if follower else None,
                           gap=follower["gap"] if follower else None,time_gap=follower["time_gap"] if follower else None,
                           gap_usable=follower["gap_usable"] if follower else False,
                           leader=follower["leader"] if follower else None,
                           follower_lane=follower["lane"] if follower else None,
                           flags=follower["flags"] if follower else ["follower_not_observed"]))
    payload = {"schema_version":1,"event":event,"frame_columns":["id","x_m","y_m","length_m","width_m","speed_mps","lane","leader_id","flagged"],"frames":packed_frames,"series":series}
    body=json.dumps(payload,separators=(",",":"),allow_nan=False).encode()
    name=f"encounter-{index}.json.gz"
    (directory/name).write_bytes(gzip.compress(body,mtime=0))
    return {"file":name,"sha256_uncompressed":hashlib.sha256(body).hexdigest(),"actor":event["actor"],"follower":event["follower"],"sample_time_s":event["t"]/1000,"repeated_candidate":event["repeated_candidate"],"prior_repeat":event["prior_repeat"],"nearby_actor_changes_s":event["nearby_actor_changes_s"],"selection_role":event["selection_role"],"old_lane":event["old_lane"],"new_lane":event["new_lane"],"coverage":event["coverage"]}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,default=ROOT/"runs/encounters/raw")
    parser.add_argument("--output",type=Path,default=ROOT/"docs/encounter-data")
    args=parser.parse_args()
    manifest=json.loads((args.input/"manifest.json").read_text())
    protocol_bytes=(ROOT/"research/encounters/protocol.json").read_bytes()
    if hashlib.sha256(protocol_bytes).hexdigest()!=manifest["protocol_sha256"]:
        raise ValueError("Protocol changed since acquisition; record and explicitly resolve the amendment")
    protocol=json.loads(protocol_bytes)
    points,counts=deduplicate(load_pages(args.input,manifest),manifest["start_ms"])
    if counts["source_rows"]!=manifest["expected_rows"]:
        raise ValueError("Source completeness failed")
    if any(t<0 or t>=protocol["sample_seconds"]*1000 or t%100 for _,t in points):
        raise ValueError("Unexpected sample time grid")
    tracks,flags=qualify(points,protocol)
    events,funnel=find_events(tracks,points,protocol)
    available=[e for e in events if e["inspectable"]]
    # Coverage first, never response magnitude or direction.
    available.sort(key=lambda e:(-min(e["coverage"][f"{name}_30s"]["present_samples"] for name in ("actor","follower")),e["t"],e["actor"]))
    selected=available[:3]
    for event in selected:
        event["selection_role"] = "predeclared coverage example"
    amendment_bytes=(ROOT/"research/encounters/selection-amendment-01.json").read_bytes()
    supplemental=[e for e in available if e["prior_repeat"] and e not in selected]
    if supplemental:
        supplemental[0]["selection_role"] = "supplemental repeated-change example (amendment 01)"
        selected.append(supplemental[0])
    frames=defaultdict(list)
    for row in points.values():
        frames[row["t"]].append(row)
    durations=[(r[-1]["t"]-r[0]["t"])/1000 for r in tracks.values()]
    gaps=sum(1 for rows in tracks.values() for a,b in zip(rows,rows[1:]) if b["t"]-a["t"]!=100)
    args.output.mkdir(parents=True,exist_ok=True)
    for stale in args.output.glob("encounter-*.json.gz"):
        stale.unlink()
    exports=[export_encounter(event,points,frames,args.output,i+1) for i,event in enumerate(selected)]
    audit={"schema_version":1,"status":"development feasibility only; no causal analysis or fitted behavior", "sample_seconds":protocol["sample_seconds"],"recording":"FHWA NGSIM I-80 eastbound, Emeryville, April 13 2005", "source":manifest["source"],"source_start_ms":manifest["start_ms"],"clock_note":"Elapsed source time is used. Earliest API timestamp converts to 15:58:55.3 PDT; FHWA names the first period 16:00–16:15. Absolute clock alignment has not been independently resolved.", "identity_namespace":f"ngsim:i80:{manifest['start_ms']}","counts":dict(counts),"vehicles":len(tracks),"observed_duration_seconds":quantiles(durations),"track_discontinuities":gaps,"row_flags":dict(flags),"candidate_funnel":dict(funnel),"encounters":exports,"protocol_sha256":manifest["protocol_sha256"],"limitations":["Five-minute development sample; not independent-day validation.","Stable lane changes are candidates, not proof of weaving, intent or aggression.","Selected cases are direct actor/follower interactions; no unexposed comparison cohort.","Raw tracking/speed measurements have not been independently reconstructed.","No causal effect, desired-headway parameter or simulation behavior has been estimated.","I-24 longer-duration sample is pending; its access page returned HTTP 502."],"attribution":{"name":"US DOT / FHWA NGSIM","dataset_url":"https://data.transportation.gov/resource/8ect-6jqj.json","license":"CC BY-SA 3.0 (API license object)","license_url":"https://creativecommons.org/licenses/by-sa/3.0/","metadata_note":"Common Core metadata separately names CC BY-SA 4.0; both source declarations are retained in the source metadata.","changes":"Bounded extraction, exact deduplication, conflict quarantine, SI conversion, derived gaps, event screening and display subsets by TrafficLab, 2026-09-27."}}
    audit["selection_amendment_sha256"] = hashlib.sha256(amendment_bytes).hexdigest()
    audit["inspectable_prior_repeat_unique_actors"] = len({e["actor"] for e in events if e["inspectable"] and e["prior_repeat"]})
    (args.output/"index.json").write_text(json.dumps(audit,indent=2,allow_nan=False)+"\n")
    research=ROOT/"research/encounters"
    (research/"acquisition-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (research/"event-audit.json").write_text(json.dumps({"events":events},indent=2)+"\n")
    (research/"source-metadata.json").write_bytes((args.input/"source-metadata.json").read_bytes())
    print(json.dumps({k:v for k,v in audit.items() if k not in ("encounters","attribution")},indent=2))


if __name__=="__main__":
    main()
