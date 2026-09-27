"""Acquire the protocol's bounded NGSIM development sample; no later intervals."""
import argparse
import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "https://data.transportation.gov/resource/8ect-6jqj.json"
FIELDS = "vehicle_id,frame_id,total_frames,global_time,local_x,local_y,v_length,v_width,v_class,v_vel,v_acc,lane_id,preceding,following,space_headway,time_headway,location"


def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "TrafficLab research feasibility sample"})
            with urllib.request.urlopen(request, timeout=50) as response:
                body = response.read(100_000_001)
                if len(body) > 100_000_000:
                    raise ValueError("Single-response byte safety limit exceeded")
                return body
        except (OSError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(1)


def query(**params):
    return API + "?" + urllib.parse.urlencode(params)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "runs/encounters/raw")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    protocol_bytes = (ROOT / "research/encounters/protocol.json").read_bytes()
    protocol = json.loads(protocol_bytes)
    metadata = fetch("https://data.transportation.gov/api/views/8ect-6jqj.json")
    (args.output / "source-metadata.json").write_bytes(metadata)
    first_url = query(**{"$select": "min(global_time) as first_time", "$where": "location='i-80'"})
    first = int(json.loads(fetch(first_url))[0]["first_time"])
    end = first + protocol["sample_seconds"] * 1000
    where = f"location='i-80' AND global_time >= {first} AND global_time < {end}"
    count_url = query(**{"$select": "count(*) as n", "$where": where})
    expected = int(json.loads(fetch(count_url))[0]["n"])
    if not 0 < expected <= 800_000:
        raise ValueError(f"Unexpected bounded sample size {expected}")
    manifest = {"schema_version": 1, "role": "development feasibility only", "retrieved_at": datetime.now(timezone.utc).isoformat(), "source": API, "first_time_query": first_url, "count_query": count_url, "start_ms": first, "end_ms_exclusive": end, "expected_rows": expected, "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(), "metadata_sha256": hashlib.sha256(metadata).hexdigest(), "files": []}
    print(f"Bounded first {protocol['sample_seconds']} seconds: {expected} source rows", flush=True)
    total = 0
    for offset in range(0, expected, 25000):
        url = query(**{"$select": FIELDS + ",:id as source_row_id", "$where": where, "$order": "global_time,vehicle_id,frame_id,:id", "$limit": 25000, "$offset": offset})
        path = args.output / f"page-{offset:07d}.json.gz"
        url_path = path.with_suffix(".url")
        if path.exists() and url_path.exists() and url_path.read_text() == url:
            body = gzip.decompress(path.read_bytes())
        else:
            body = fetch(url)
            path.write_bytes(gzip.compress(body, mtime=0))
            url_path.write_text(url)
        rows = json.loads(body)
        if len(rows) != min(25000, expected - offset):
            raise ValueError("Incomplete page; do not analyze")
        total += len(rows)
        manifest["files"].append({"file": path.name, "url": url, "rows": len(rows), "sha256_uncompressed": hashlib.sha256(body).hexdigest()})
        print(f"Acquired {total}/{expected}", flush=True)
    after = int(json.loads(fetch(count_url))[0]["n"])
    if total != expected or after != expected:
        raise ValueError("Query completeness/source count changed; do not analyze")
    manifest["acquired_rows"] = total
    manifest["count_rechecked"] = after
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Acquisition complete with hashes and count verification", flush=True)


if __name__ == "__main__":
    main()
