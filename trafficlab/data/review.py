"""Deterministic observation review and provisional geometry matching.

Candidates are never promoted to verified detector locations automatically.
"""
import argparse
from collections import Counter
from datetime import date
from copy import deepcopy
import json
from pathlib import Path

from .pems import digest


def review(bundle, network):
    import sumolib
    data = deepcopy(bundle)
    net = sumolib.net.readNet(str(network))
    groups = {s['id']: [] for s in data['stations']}
    for row in data['records']:
        groups[row['station_id']].append(row)
    summaries = []
    for station in data['stations']:
        records = groups[station['id']]
        station['network_xy'] = list(net.convertLonLat2XY(station['longitude'], station['latitude']))
        candidates = []
        # Mainline only. Ramp shape heading alone cannot identify the parent
        # freeway direction or distinguish on/off ramps at shared coordinates.
        if station['type'] == 'ML':
            axis = {'E': (1, 0), 'W': (-1, 0), 'N': (0, 1), 'S': (0, -1)}[station['direction']]
            for edge in net.getEdges():
                if edge.getType() != 'highway.motorway':
                    continue
                shape = edge.getShape()
                heading = (shape[-1][0]-shape[0][0], shape[-1][1]-shape[0][1])
                if sum(a*b for a,b in zip(axis, heading)) <= 0:
                    continue
                offset, distance = sumolib.geomhelper.polygonOffsetAndDistanceToPoint(station['network_xy'], shape)
                candidates.append({'edge': edge.getID(), 'distance_m': round(distance, 2),
                                   'offset_m': round(offset, 2), 'network_lanes': edge.getLaneNumber()})
            candidates.sort(key=lambda c: (c['distance_m'], c['edge']))
        station['mapping_candidates'] = candidates[:2]
        station['sumo_edge'] = None
        station['mapping_status'] = 'provisional mainline candidates; not certified' if candidates else 'ramp topology review required; no edge assigned'
        flags = []
        if candidates:
            if candidates[0]['distance_m'] > 30: flags.append('distant_candidate')
            if candidates[0]['network_lanes'] != station['lanes']: flags.append('lane_count_mismatch')
            if len(candidates)>1 and candidates[1]['distance_m']-candidates[0]['distance_m']<10: flags.append('nearby_alternative_edge')
        station['mapping_flags'] = flags
        summaries.append({'station_id': station['id'], 'name': station['name'], 'type': station['type'],
                          'direction': station['direction'], 'rows': len(records),
                          'valid_speed': sum(r['speed_mph'] is not None for r in records),
                          'valid_flow': sum(r['flow_vehicles_per_5min'] is not None for r in records),
                          'fully_observed': sum(r['percent_observed'] == 100 for r in records),
                          'zero_percent_observed': sum(r['percent_observed'] == 0 for r in records),
                          'quality_flags': dict(sorted(Counter(f for r in records for f in r['quality_flags']).items()))})
    data['network_context'] = {'source': 'OpenStreetMap via frozen SUMO network',
                               'network_sha256': digest(network),
                               'edges': [{'id':e.getID(),'type':e.getType(),'shape':e.getShape()} for e in net.getEdges()]}
    data['review'] = {'stations': summaries, 'metadata_age_days':
                     (date.fromisoformat(data['date']) - date.fromisoformat(data['provenance']['metadata_effective_date'])).days,
                     'interpretation': ['A present row can contain no usable values.',
                       'Percent observed is retained as reported; 100% does not independently validate speed.',
                       'Missing ramp speed is not assumed to be a detector fault.',
                       'No station counts are summed into a corridor total: the same vehicles cross multiple stations.',
                       'Candidate edge matches are spatial inferences, not verified detector placements.']}
    data['limitations'].append('Metadata predates observations; matching ID/direction/type does not verify unchanged location or lanes.')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--network', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(json.loads(args.input.read_text()), args.network)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False))
    print(f'Reviewed {len(result["stations"])} stations; no candidate match certified.')

if __name__ == '__main__':
    main()
