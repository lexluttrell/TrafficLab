"""Observation-driven SUMO through-traffic baseline. No parameter calibration."""
import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import xml.etree.ElementTree as ET

from .comparison import aggregate_lanes, diagnostics
from .context import roads
from .data.pems import digest
from .demand import build
from .network import binary


def read_bundle(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def build_departures(count, begin, rng):
    if count is None or count < 0:
        raise ValueError('Missing or invalid entry count; no zero substitution is allowed.')
    n = int(count + 0.5)
    return sorted(begin + rng.random()*300 for _ in range(n))


def run(scenario, observations, output, seed=None):
    import sumolib
    output = output.resolve(); output.mkdir(parents=True, exist_ok=True)
    config = json.loads((scenario/'historical.json').read_text())
    geometry = json.loads((scenario/'scenario.json').read_text())
    bundle = read_bundle(observations)
    if bundle['date'] != config['date']:
        raise ValueError('Observation date does not match the configured run.')
    seed = config['seed'] if seed is None else seed
    network = (scenario/'network.net.xml').resolve()
    net, through_routes = build(network, output/'unused-synthetic.rou.xml', geometry)
    (output/'unused-synthetic.rou.xml').unlink()
    stations = {s['id']: s for s in bundle['stations']}
    rows = {(r['station_id'], r['timestamp_local'][:19]):r for r in bundle['records']}
    start = datetime.fromisoformat(config['date']+'T'+config['start_local'])
    root = ET.Element('routes')
    ET.SubElement(root, 'vType', id='baseline-car', vClass='passenger', carFollowModel='Krauss',
                  accel='2.6', decel='4.5', sigma='0.5', tau='1.0', length='5', minGap='2.5', maxSpeed='33.33')
    rng = random.Random(seed); departures = []; inputs = []; chosen_routes = []
    for sid in config['input_stations']:
        s = stations[sid]; candidate = s['mapping_candidates'][0]
        if candidate['distance_m'] > 15 or candidate['network_lanes'] != s['lanes']:
            raise ValueError('Input station binding fails distance/lane check: '+sid)
        route = next(r for r in through_routes if candidate['edge'] in r['edges'])
        edges = route['edges'][route['edges'].index(candidate['edge']):]
        rid = 'from-'+sid; pos = candidate['offset_m']+10
        if pos >= net.getEdge(edges[0]).getLength()-5:
            raise ValueError('Entry position is too close to edge end: '+sid)
        ET.SubElement(root, 'route', id=rid, edges=' '.join(edges))
        chosen_routes.append({'id':rid,'edges':edges,'input_station':sid,'depart_position_m':pos})
        for begin in range(0, config['duration_seconds'], 300):
            stamp=(start+timedelta(seconds=begin)).isoformat()
            row = rows.get((sid,stamp))
            if row is None: raise ValueError('Missing entry interval: '+sid+' '+stamp)
            times = build_departures(row['flow_vehicles_per_5min'], begin, rng)
            inputs.append({'station_id':sid,'begin':begin,'timestamp_local':stamp,
                           'reported_count':row['flow_vehicles_per_5min'],'scheduled_count':len(times),
                           'percent_observed':row['percent_observed'],'quality_flags':row['quality_flags']})
            for i, depart in enumerate(times):
                departures.append((depart, sid, begin, i, rid, pos))
    for depart,sid,begin,i,rid,pos in sorted(departures):
        ET.SubElement(root,'vehicle',id=f'p{sid}-{begin}-{i}',type='baseline-car',route=rid,
                      depart=f'{depart:.3f}',departPos=str(pos),departLane='free',departSpeed='max')
    demand = output/'demand.rou.xml'; ET.ElementTree(root).write(demand,encoding='utf-8',xml_declaration=True)
    additional = ET.Element('additional'); bindings=[]; lane_counts={}
    for sid,s in stations.items():
        if s['type']!='ML' or sid in config['input_stations'] or sid in config['excluded_stations']:
            continue
        c=s['mapping_candidates'][0]; eid=c['edge']
        if not any(eid in r['edges'] for r in chosen_routes):continue
        if c['distance_m']>15 or c['network_lanes']!=s['lanes'] or s['mapping_flags']:
            continue
        edge=net.getEdge(eid); lane_counts[sid]=len(edge.getLanes()); lane_positions=[]
        for lane in edge.getLanes():
            offset,_=sumolib.geomhelper.polygonOffsetAndDistanceToPoint(s['network_xy'],lane.getShape())
            shape_length=sumolib.geomhelper.polyLength(lane.getShape())
            pos=max(.1,min(lane.getLength()-.1,offset*lane.getLength()/shape_length))
            lane_positions.append({'lane':lane.getID(),'position_m':pos})
            ET.SubElement(additional,'inductionLoop',id=sid+'_'+str(lane.getIndex()),lane=lane.getID(),
                          pos=str(pos),period='300',file=str(output/'detectors.xml'))
        bindings.append({'id':sid,'name':s['name'],'direction':s['direction'],'edge':eid,
                         'network_xy':s['network_xy'],'distance_m':c['distance_m'],
                         'status':'provisional spatial/topological model binding; not field certified','lanes':lane_positions})
    detectors = output/'detectors.add.xml';ET.ElementTree(additional).write(detectors,encoding='utf-8',xml_declaration=True)
    cmd=[binary('sumo'),'-n',str(network),'-r',str(demand),'-a',str(detectors),'--seed',str(seed),
         '--step-length','0.2','--end',str(config['duration_seconds']),
         '--fcd-output',str(output/'fcd.xml.gz'),'--device.fcd.period',str(config['sample_seconds']),
         '--device.fcd.begin',str(config['replay_begin_seconds']),'--fcd-output.acceleration','true',
         '--tripinfo-output',str(output/'trips.xml'),'--summary-output',str(output/'summary.xml'),
         '--no-step-log','true','--log',str(output/'sumo.log'),'--time-to-teleport','-1']
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL)
    grouped=defaultdict(list)
    for interval in ET.parse(output/'detectors.xml').getroot():
        if interval.tag=='interval':
            r=interval.attrib;grouped[(r['id'].rsplit('_',1)[0],int(float(r['begin'])))].append(r)
    comparison=[]
    for (sid,begin),lanes in sorted(grouped.items()):
        if len(lanes)!=lane_counts[sid]:raise ValueError('Incomplete simulated station aggregation')
        stamp=(start+timedelta(seconds=begin)).isoformat(); obs=rows.get((sid,stamp))
        reasons=[]
        if begin<config['warmup_seconds']:reasons.append('warmup')
        if obs is None:reasons.append('missing_source_row')
        elif obs['percent_observed']!=100 or obs['quality_flags']:reasons.append('source_quality')
        comparison.append({'station_id':sid,'begin':begin,'end':begin+300,'timestamp_local':stamp,
                           'simulated':aggregate_lanes(lanes),
                           'observed':{'count':obs['flow_vehicles_per_5min'] if obs else None,
                                       'speed_mph':obs['speed_mph'] if obs else None,
                                       'occupancy_fraction':obs['occupancy_fraction'] if obs else None},
                           'percent_observed':obs['percent_observed'] if obs else None,
                           'eligible':not reasons,'excluded_reasons':reasons})
    frames=[]
    with gzip.open(output/'fcd.xml.gz','rb') as stream:
        for _,e in ET.iterparse(stream,events=('end',)):
            if e.tag!='timestep':continue
            time=float(e.attrib['time'])
            if config['replay_begin_seconds']<=time<=config['replay_end_seconds']:
                vehicles=[[v.attrib['id'],round(float(v.attrib['x']),1),round(float(v.attrib['y']),1),
                           round(float(v.attrib['speed']),2),round(float(v.attrib['angle']),1),
                           v.attrib['lane'],round(float(v.attrib['pos']),1),round(float(v.attrib.get('acceleration',0)),2)] for v in e]
                frames.append({'time':time-config['replay_begin_seconds'],'vehicles':vehicles})
            e.clear()
    last=ET.parse(output/'summary.xml').getroot()[-1].attrib
    trips=ET.parse(output/'trips.xml').getroot()
    report={'scheduled':len(departures),'completed_trips':len(trips),
            **{k:int(last.get(k,0)) for k in ['inserted','running','waiting','teleports','collisions']}}
    report['not_inserted']=report['scheduled']-report['inserted']
    report['mean_depart_delay_s']=sum(float(t.attrib['departDelay']) for t in trips)/len(trips) if len(trips) else None
    meta={'scenario':geometry['name']+' · historical-count baseline','seed':seed,
          'scientific_status':'HISTORICAL COUNTS · THROUGH-ONLY · UNCALIBRATED',
          'sumo_version':subprocess.check_output([binary('sumo'),'--version'],text=True).splitlines()[0],
          'source_date':config['date'],'start_local':start.isoformat(),'replay_start_local':(start+timedelta(seconds=config['replay_begin_seconds'])).isoformat(),
          'sample_seconds':config['sample_seconds'],'replay_offset_seconds':config['replay_begin_seconds'],
          'network_sha256':digest(network),'observations_sha256':digest(observations),'demand_sha256':digest(demand),
          'scenario_config_sha256':digest(scenario/'historical.json'),
          'source_provenance':bundle['provenance'],'report':report,'routes':chosen_routes,
          'assumptions':[config['demand_scope'],'Entry flow is counted at internal model boundaries, not unconstrained upstream travel demand.',
                         'Departures are uniformly randomized within each five-minute bin with fixed seed; counts rounded to nearest integer.',
                         'Eastbound input station 400865 is partially observed (75%); source estimation is retained.',
                         'Single passenger-car population uses uncalibrated Krauss parameters; entry speed is model free speed, not measured speed.',
                         'SUMO loop speeds use count-weighted arithmetic means; real detector estimation may differ.',
                         'Timestamp interval start follows documented PeMS schema; source-local clock used without UTC alignment.',
                         '15-minute warm-up is an assumption; sensitivity not tested.',
                         'Lane-count/ambiguous bindings excluded; remaining bindings are provisional.',
                         'No fitting, no held-out validation, no inferred causal explanation for observed slowdown.'],
          'command':cmd[1:], 'vehicle_columns':['id','x_m','y_m','speed_m_s','angle_deg','lane','lane_position_m','acceleration_m_s2']}
    payload={'meta':meta,'frames':frames,'lanes':[{'id':l.getID(),'shape':l.getShape(),'width':l.getWidth(),'name':e.getName(),'speed':l.getSpeed()} for e in net.getEdges() for l in e.getLanes()],
             'context_labels':geometry.get('context_labels',[]),'context_roads':roads(scenario/'source.osm.xml',net),
             'comparison':{'stations':bindings,'records':comparison,'metrics':diagnostics(comparison),'inputs':inputs,
                           'input_markers':[{'id':sid,'network_xy':stations[sid]['network_xy'],'direction':stations[sid]['direction']} for sid in config['input_stations']]}}
    (output/'replay.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False))
    (output/'replay.json.gz').write_bytes(gzip.compress((output/'replay.json').read_bytes(),mtime=0))
    (output/'manifest.json').write_text(json.dumps(meta,indent=2,allow_nan=False))
    (output/'comparison.json').write_text(json.dumps(payload['comparison'],indent=2,allow_nan=False))
    print(json.dumps({'report':report,'diagnostics':payload['comparison']['metrics'],'frames':len(frames),'compressed_bytes':(output/'replay.json.gz').stat().st_size},indent=2))
    return payload


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scenario',type=Path,default=Path(__file__).resolve().parents[1]/'scenarios/pinole')
    p.add_argument('--observations',type=Path,required=True)
    p.add_argument('--output',type=Path,default=Path('runs/historical'))
    p.add_argument('--seed',type=int)
    a=p.parse_args();run(a.scenario,a.observations,a.output,a.seed)

if __name__=='__main__':main()
