"""Predeclared geometry/seed check; no parameter optimization or held-out claims.
Run: python -m scripts.merge_sensitivity --seeds 42 43
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from trafficlab.network import binary
from trafficlab.data.review import review
from trafficlab.historical import run

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def percentile(values,q):
    ordered=sorted(values)
    if not ordered:return None
    i=(len(ordered)-1)*q;lo=int(i);hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(i-lo)

def case(length,seed):
    base=ROOT/'scenarios/pinole-ramps';original=ROOT/'scenarios/pinole-merge'
    folder=ROOT/f'runs/sensitivity/l{length}-s{seed}';scenario=folder/'scenario';scenario.mkdir(parents=True,exist_ok=True)
    (folder/'result.json').unlink(missing_ok=True)
    geometry=json.loads((original/'scenario.json').read_text());geometry['context_source']=str(base/'source.osm.xml.gz');geometry['name']=f'Pinole · assumed {length} m merges · seed {seed}'
    (scenario/'scenario.json').write_text(json.dumps(geometry,indent=2))
    config=json.loads((original/'historical.json').read_text());config['seed']=seed
    config['demand_scope']=config['demand_scope'].replace('150 m',f'{length} m')
    (scenario/'historical.json').write_text(json.dumps(config,indent=2))
    cmd=[binary('netconvert'),'--osm-files',str(base/'source.osm.xml.gz'),'--keep-edges.by-type','highway.motorway,highway.motorway_link',
         '--remove-edges.isolated','true','--output.street-names','true','--ramps.set','1193463509#1,23978795#1',
         '--ramps.ramp-length',str(length),'--output-file',str(scenario/'network.net.xml')]
    result=subprocess.run(cmd,capture_output=True,text=True);(scenario/'conversion.log').write_text(result.stdout+result.stderr);result.check_returncode()
    bundle=review(json.loads(gzip.decompress((base/'observations.json.gz').read_bytes())),scenario/'network.net.xml')
    observations=scenario/'observations.json.gz';observations.write_bytes(gzip.compress(json.dumps(bundle,separators=(',',':')).encode(),mtime=0))
    payload=run(scenario,observations,folder/'output')
    meta=payload['meta'];report=meta['report'];drain=meta['drain_report']
    summary=list(ET.parse(folder/'output/summary.xml').getroot())
    safety={'no_collisions_at_any_step':all(int(s.get('collisions','0'))==0 for s in summary),
            'no_teleports_at_any_step':all(int(s.get('teleports','0'))==0 for s in summary)}
    trips=list(ET.parse(folder/'output/trips.xml').getroot())
    origins=[]
    for o in drain['origins']:
        group=[t for t in trips if t.get('id').split('-')[0][1:]==o['station'] and float(t.get('arrival'))>=0]
        origins.append({**o,'mean_time_s':sum(float(t.get('duration')) for t in group)/len(group) if group else None,
                        'p95_time_s':percentile([float(t.get('duration')) for t in group],.95),
                        'p95_waiting_s':percentile([float(t.get('waitingTime')) for t in group],.95)})
    vehicles=ET.parse(folder/'output/demand.rou.xml').getroot().findall('vehicle')
    schedule=[(v.get('id'),v.get('depart')) for v in vehicles]
    eligible=sorted((r['station_id'],r['begin']) for r in payload['comparison']['records'] if r['eligible'])
    import sumolib
    net=sumolib.net.readNet(str(scenario/'network.net.xml'))
    acceleration_lanes=[]
    for edge in ['1193463509#1-AddedOnRampEdge','23978795#1-AddedOnRampEdge']:
        lane=net.getEdge(edge).getLane(0);acceleration_lanes.append({'edge':edge,'actual_lane_length_m':lane.getLength()})
    output={'length_setting_m':length,'seed':seed,'report':report,'drain':drain,'safety':safety,
            'origins':origins,'metrics':payload['comparison']['metrics'],'eligible_station_bins':eligible,
            'departure_schedule_sha256':hashlib.sha256(json.dumps(schedule,separators=(',',':')).encode()).hexdigest(),
            'source_osm_gzip_sha256':digest(base/'source.osm.xml.gz'),'source_aggregate_sha256':digest(base/'observations.json.gz'),
            'network_sha256':digest(scenario/'network.net.xml'),'config_sha256':digest(scenario/'historical.json'),
            'sumo_version':meta['sumo_version'],'acceleration_lanes':acceleration_lanes}
    (folder/'result.json').write_text(json.dumps(output,indent=2))
    print(f'Completed {length} m / seed {seed}: {drain["completed"]}/{drain["scheduled"]} trips',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,nargs='+',default=[42,43]);p.add_argument('--lengths',type=int,nargs='+',default=[100,150,200]);args=p.parse_args()
    for length in args.lengths:
        for seed in args.seeds:case(length,seed)
