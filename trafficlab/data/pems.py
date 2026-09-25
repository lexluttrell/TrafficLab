"""Strict, date-scoped PeMS clearinghouse adapter. No login or imputation.

Schema reference: SANDAG/PeMS-Datasets, commit
 e6e125f65e45afdeceaebc4d6d0b5c92effa9e47, python/extract_parquet.py.
District 4 production acceptance awaits real authorized source files.
"""
import argparse
import csv
from datetime import date, datetime, time, timedelta, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = 'trafficlab.observations.v1'
ZONE = ZoneInfo('America/Los_Angeles')


def open_text(path):
    return gzip.open(path, 'rt', encoding='utf-8-sig', newline='') if path.suffix == '.gz' else path.open('r', encoding='utf-8-sig', newline='')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def day_grid(day):
    start = datetime.combine(day, time(), ZONE)
    end = datetime.combine(day + timedelta(days=1), time(), ZONE)
    if start.utcoffset() != end.utcoffset():
        raise ValueError('DST transition days are not supported yet; choose a non-transition date.')
    return [(start + timedelta(minutes=5*i)).isoformat() for i in range(288)]


def number(raw, name, flags, lower=0, upper=None, integer=False):
    if not raw.strip():
        flags.append('missing_' + name)
        return None
    try:
        value = float(raw)
        if not math.isfinite(value) or value < lower or (upper is not None and value > upper) or (integer and not value.is_integer()):
            raise ValueError()
        return int(value) if integer else value
    except ValueError:
        flags.append('invalid_' + name)
        return None


def stations_from(path, district, freeway, bbox):
    stations = {}
    excluded_location = 0
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError('Invalid bounding box: west,south,east,north required.')
    with open_text(path) as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        required = {'ID', 'Fwy', 'Dir', 'District', 'Latitude', 'Longitude', 'Type', 'Lanes', 'Name'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Metadata must be the tab-separated PeMS Station Metadata export with named header columns.')
        for line, row in enumerate(reader, 2):
            try:
                if int(row['District']) != district or int(row['Fwy']) != freeway:
                    continue
                lat, lon = float(row['Latitude']), float(row['Longitude'])
                if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError()
            except (ValueError, TypeError):
                excluded_location += 1
                continue
            if not (west <= lon <= east and south <= lat <= north):
                continue
            sid = str(int(row['ID']))
            if sid in stations:
                raise ValueError(f'Duplicate selected metadata station {sid}, line {line}')
            if row['Dir'] not in ('N', 'S', 'E', 'W') or not row['Type']:
                raise ValueError(f'Invalid station direction/type at metadata line {line}')
            stations[sid] = {'id': sid, 'name': row['Name'], 'latitude': lat, 'longitude': lon,
                             'district': district, 'freeway': freeway, 'direction': row['Dir'],
                             'type': row['Type'], 'lanes': int(row['Lanes']),
                             'absolute_postmile': row.get('Abs_PM'), 'sumo_edge': None,
                             'mapping_status': 'geographic candidate; edge/direction review pending'}
    if not stations:
        raise ValueError('No stations selected. Check metadata, freeway/district and scenario bounds.')
    return stations, excluded_location


def normalize(metadata, observations, day, metadata_date, bbox, district=4, freeway=80):
    if metadata_date > day:
        raise ValueError('Metadata effective date cannot be later than the observation date.')
    grid = day_grid(day)
    stations, excluded = stations_from(metadata, district, freeway, bbox)
    records = {}
    duplicates = 0
    with open_text(observations) as stream:
        for line, row in enumerate(csv.reader(stream), 1):
            if not row:
                continue
            if len(row) < 12 or (len(row)-12) % 5:
                raise ValueError(f'Invalid station_5min field count at line {line}; expected 12 + 5 per lane.')
            sid = row[1].strip()
            if sid not in stations:
                continue
            stamp = datetime.strptime(row[0], '%m/%d/%Y %H:%M:%S')
            if stamp.date() != day:
                continue
            if stamp.second or stamp.minute % 5:
                raise ValueError(f'Off-grid timestamp at line {line}')
            station = stations[sid]
            if (int(row[2]), int(row[3]), row[4], row[5]) != (district, freeway, station['direction'], station['type']):
                raise ValueError(f'Station metadata mismatch at line {line}, station {sid}')
            flags = []
            record = {'station_id': sid, 'timestamp_local': stamp.replace(tzinfo=ZONE).isoformat(),
                      'timestamp_utc': stamp.replace(tzinfo=ZONE).astimezone(timezone.utc).isoformat(),
                      'samples': number(row[7], 'samples', flags, integer=True),
                      'percent_observed': number(row[8], 'percent_observed', flags, upper=100),
                      'flow_vehicles_per_5min': number(row[9], 'flow', flags),
                      'occupancy_fraction': number(row[10], 'occupancy', flags, upper=1),
                      'speed_mph': number(row[11], 'speed', flags),
                      'raw_station_values': row[6:12], 'raw_lane_values': row[12:]}
            if record['percent_observed'] is not None and record['percent_observed'] < 100:
                flags.append('partially_observed_or_imputed')
            if record['samples'] == 0:
                flags.append('zero_samples')
            record['quality_flags'] = flags
            key = (sid, record['timestamp_local'])
            if key in records:
                if records[key] != record:
                    raise ValueError(f'Conflicting duplicate for station {sid} at {stamp}')
                duplicates += 1
            records[key] = record
    if not records:
        raise ValueError('No selected observations for this date. No empty historical dataset was produced.')
    ordered = [records[k] for k in sorted(records)]
    coverage = []
    for sid in sorted(stations):
        rows = [r for r in ordered if r['station_id'] == sid]
        present = {r['timestamp_local'] for r in rows}
        coverage.append({'station_id': sid, 'expected_intervals': len(grid), 'present_intervals': len(rows),
                         'missing_intervals': [t for t in grid if t not in present],
                         'flagged_intervals': sum(bool(r['quality_flags']) for r in rows),
                         'valid_speed_intervals': sum(r['speed_mph'] is not None for r in rows)})
    return {'schema': SCHEMA, 'kind': 'reported_detector_observations', 'date': day.isoformat(),
            'timezone': str(ZONE), 'interval_seconds': 300, 'interval_anchor': 'source convention requires verification',
            'expected_timestamps': grid, 'stations': [stations[k] for k in sorted(stations)],
            'records': ordered, 'coverage': coverage,
            'provenance': {'adapter': 'pems-station-5min-v1', 'metadata_sha256': digest(metadata),
                           'observations_sha256': digest(observations), 'metadata_effective_date': metadata_date.isoformat(),
                           'district': district, 'freeway': freeway, 'bbox': list(bbox),
                           'identical_duplicates_removed': duplicates,
                           'metadata_rows_excluded_invalid_location_or_route_fields': excluded,
                           'source': 'User-supplied PeMS clearinghouse files; verify origin before scientific use',
                           'timezone_assumption': 'PeMS local civil timestamps interpreted as America/Los_Angeles; confirm for supplied archive',
                           'raw_data_published': False},
            'limitations': ['No calibration or held-out validation.', 'Detector aggregates do not identify individual vehicles.',
                            'Reported speeds may be estimated; percent observed is retained, not used to silently discard rows.',
                            'Station-to-SUMO-edge mapping and timestamp anchoring require review against actual source files.']}


def main():
    parser = argparse.ArgumentParser(description='Import a local PeMS five-minute archive; never uploads data.')
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--observations', type=Path, required=True)
    parser.add_argument('--date', type=date.fromisoformat, required=True)
    parser.add_argument('--metadata-date', type=date.fromisoformat, required=True)
    parser.add_argument('--scenario', type=Path, default=Path(__file__).resolve().parents[2]/'scenarios/pinole/scenario.json')
    parser.add_argument('--district', type=int, default=4)
    parser.add_argument('--freeway', type=int, default=80)
    parser.add_argument('--output', type=Path, default=Path('runs/observations/observations.json'))
    args = parser.parse_args()
    config = json.loads(args.scenario.read_text())
    try:
        data = normalize(args.metadata, args.observations, args.date, args.metadata_date, config['bbox'], args.district, args.freeway)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(2, f'Import failed: {error}\n')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    receipt = {'imported_at_utc': datetime.now(timezone.utc).isoformat(), 'normalized_sha256': digest(args.output)}
    args.output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2))
    print(f'Imported {len(data["records"])} records at {len(data["stations"])} stations into {args.output}')

if __name__ == '__main__':
    main()
