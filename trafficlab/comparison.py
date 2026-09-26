"""Detector diagnostics, separate from traffic generation and parameter fitting."""
import math

MPH_PER_MPS = 2.2369362920544


def aggregate_lanes(lanes):
    """SUMO E1 counts and vehicle-weighted time-mean speed, not corridor speed."""
    counts = [int(r['nVehContrib']) for r in lanes]
    total = sum(counts)
    valid = [(n, float(r['speed'])) for n, r in zip(counts, lanes) if n > 0 and float(r['speed']) >= 0]
    speed = sum(n*v for n,v in valid)/sum(n for n,_ in valid)*MPH_PER_MPS if valid else None
    return {'count': total, 'speed_mph': speed,
            'occupancy_fraction': sum(float(r['occupancy']) for r in lanes)/len(lanes)/100 if lanes else None}


def diagnostics(records):
    """Only qualified independent-of-input station bins; no missing-value fill."""
    selected = [r for r in records if r['eligible']]
    result = {'eligible_bins': len(selected), 'scope': 'same-day diagnostic; not held-out validation'}
    for key in ('count', 'speed_mph'):
        pairs = [(r['simulated'][key], r['observed'][key]) for r in selected
                 if r['simulated'][key] is not None and r['observed'][key] is not None]
        errors = [s-o for s,o in pairs]
        result[key] = {'bins':len(pairs), 'mae':sum(abs(e) for e in errors)/len(errors) if errors else None,
                       'rmse':math.sqrt(sum(e*e for e in errors)/len(errors)) if errors else None,
                       'bias':sum(errors)/len(errors) if errors else None}
        if key == 'count':
            denominator=sum(o for _,o in pairs)
            result[key]['wape_percent'] = 100*sum(abs(e) for e in errors)/denominator if denominator else None
    return result
