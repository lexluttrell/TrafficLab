"""Paired single-car SUMO experiments. Never fits or accesses held-out data."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
from .comparison import aggregate_lanes, diagnostics
from .network import binary

ROOT=Path(__file__).resolve().parents[1]
SCENARIO=ROOT/'scenarios/pinole-merge'
CONFIG=SCENARIO/'driver-experiment.json'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def key(tau,pace):return f'h{int(tau*10)}-p{int(pace*100)}'
def write_gzip(path,value):
    path.write_bytes(gzip.compress(canonical(value),mtime=0))
    return {'file':path.name,'sha256':digest(path),'bytes':path.stat().st_size}

def trip_metrics(trips,ids):
    if not ids:raise ValueError('Empty outcome cohort')
    if any(i not in trips or float(trips[i]['arrival'])<0 for i in ids):
        raise ValueError('Incomplete cohort: no completed-only effect estimate allowed')
    rows=[trips[i] for i in ids]
    times=[float(t['duration'])+float(t['departDelay']) for t in rows]
    return {'n':len(rows),'mean_trip_s':sum(times)/len(times),'total_trip_s':sum(times),
            'mean_waiting_s':sum(float(t['waitingTime']) for t in rows)/len(rows)}

def prepare(base):
    if not (base/'replay.json').exists():
        from .historical import run
        run(SCENARIO,SCENARIO/'observations.json.gz',base)
    p=json.loads((base/'replay.json').read_text())
    for field,path in [('network_sha256',SCENARIO/'network.net.xml'),('observations_sha256',SCENARIO/'observations.json.gz'),('demand_sha256',base/'demand.rou.xml')]:
        if p['meta'][field]!=digest(path):raise ValueError('Base input changed: '+field)
    if p['meta']['seed']!=42:raise ValueError('Fixed demand realization requires seed 42')
    return p

def members(vehicles,rule,exclude=None):
    return [v.get('id') for v in vehicles if v.get('id').startswith('o'+rule['origin']+'-')
            and rule['begin']<=float(v.get('depart'))<rule['end'] and v.get('id')!=exclude]

def run_case(base,output,config,template,tau,pace,seed):
    output.mkdir(parents=True,exist_ok=True);(output/'result.json').unlink(missing_ok=True)
    demand=ET.parse(base/'demand.rou.xml').getroot();vehicles=demand.findall('vehicle')
    target=next(v for v in vehicles if v.get('id')==config['target_id']);departure=float(target.get('depart'))
    vtype=deepcopy(demand.find('vType'));vtype.set('id','experiment-car');vtype.set('tau',str(tau));demand.insert(1,vtype)
    target.set('type','experiment-car');target.set('speedFactor',str(pace))
    ET.ElementTree(demand).write(output/'demand.rou.xml',encoding='utf-8',xml_declaration=True)
    contract=[{k:v for k,v in x.attrib.items() if k not in ('type','speedFactor')} for x in vehicles]
    routes=[x.attrib for x in demand.findall('route')]
    cohort=members(vehicles,config['cohort'],config['target_id'])
    detectors=ET.parse(base/'detectors.add.xml').getroot()
    for d in detectors:d.set('file',str(output/'detectors.xml'))
    ET.ElementTree(detectors).write(output/'detectors.add.xml',encoding='utf-8')
    cmd=[binary('sumo'),'-n',str(SCENARIO/'network.net.xml'),'-r',str(output/'demand.rou.xml'),'-a',str(output/'detectors.add.xml'),
         '--seed',str(seed),'--step-length','0.2','--end',str(config['end']),'--time-to-teleport','-1','--no-step-log','true',
         '--tripinfo-output',str(output/'trips.xml'),'--tripinfo-output.write-unfinished','true','--summary-output',str(output/'summary.xml'),
         '--lanechange-output',str(output/'lanechanges.xml'),'--fcd-output',str(output/'fcd.xml.gz'),
         '--device.fcd.begin',str(config['replay_begin']),'--device.fcd.period',str(config['replay_period']),
         '--fcd-output.acceleration','true','--fcd-output.max-leader-distance','200','--log',str(output/'sumo.log')]
    proc=subprocess.run(cmd,capture_output=True,text=True);(output/'stderr.log').write_text(proc.stderr);proc.check_returncode()
    trips={t.get('id'):t.attrib for t in ET.parse(output/'trips.xml').getroot() if t.tag=='tripinfo'}
    steps=list(ET.parse(output/'summary.xml').getroot());last=steps[-1]
    accounting={k:int(last.get(k,'0')) for k in ['inserted','ended','running','waiting']}
    accounting.update(scheduled=len(vehicles),collisions=max(int(s.get('collisions','0')) for s in steps),teleports=max(int(s.get('teleports','0')) for s in steps))
    if set(trips)!={v.get('id') for v in vehicles} or accounting['ended']!=len(vehicles) or any(accounting[k] for k in ['running','waiting','collisions','teleports']):
        raise ValueError('Completion/safety gate failed: '+str(accounting))
    ids=sorted(trips);id_lookup={s:i for i,s in enumerate(ids)}
    import sumolib
    net=sumolib.net.readNet(str(SCENARIO/'network.net.xml'),withInternal=True)
    lane_ids=sorted(l.getID() for e in net.getEdges(withInternal=True) for l in e.getLanes());lane_lookup={s:i for i,s in enumerate(lane_ids)}
    frames=[];series=[];before=hashlib.sha256()
    with gzip.open(output/'fcd.xml.gz','rb') as stream:
        for _,elem in ET.iterparse(stream,events=('end',)):
            if elem.tag!='timestep':continue
            t=float(elem.get('time'))
            if t>config['replay_end']:break
            cars=[]
            for v in elem:
                a=v.attrib
                cars.append([id_lookup[a['id']],float(a['x']),float(a['y']),float(a['speed']),float(a['angle']),lane_lookup[a['lane']],float(a['pos'])])
                if a['id']==config['target_id']:
                    leader=a.get('leaderID','');gap=float(a['leaderGap']) if leader else None
                    series.append({'t':t,'speed':float(a['speed']),'acceleration':float(a['acceleration']),'leader':leader or None,'gap_m':gap,
                                   'time_gap_s':gap/float(a['speed']) if gap is not None and float(a['speed'])>=2 else None})
            cars.sort(key=lambda c:c[0])
            if t<departure:before.update(canonical([t,cars]))
            frames.append({'t':t,'cars':cars});elem.clear()
    changes=[x.attrib for x in ET.parse(output/'lanechanges.xml').getroot() if x.tag=='change' and x.get('id')==config['target_id']]
    grouped=defaultdict(list)
    for x in ET.parse(output/'detectors.xml').getroot():
        if x.tag=='interval':grouped[(x.get('id').rsplit('_',1)[0],int(float(x.get('begin'))))].append(x.attrib)
    records=deepcopy(template['comparison']['records'])
    for row in records:
        raw=grouped[(row['station_id'],row['begin'])];expected=sum(d.get('id').rsplit('_',1)[0]==row['station_id'] for d in detectors)
        if len(raw)!=expected or not raw:raise ValueError('Detector lane coverage changed')
        row['simulated']=aggregate_lanes(raw)
    result={'key':key(tau,pace),'seed':seed,'tau':tau,'speedFactor':pace,'target':config['target_id'],
            'target_depart_s':float(trips[config['target_id']]['depart']),'target_arrival_s':float(trips[config['target_id']]['arrival']),
            'target_trip':trip_metrics(trips,[config['target_id']]),'target_lane_changes':changes,
            'cohort':trip_metrics(trips,cohort),'others':trip_metrics(trips,[i for i in ids if i!=config['target_id']]),
            'cohort_ids_sha256':hashlib.sha256(canonical(sorted(cohort))).hexdigest(),'accounting':accounting,'diagnostics':diagnostics(records),
            'scored_bins':[[r['station_id'],r['begin']] for r in records if r['eligible']],'scored_records':[r for r in records if r['eligible']],
            'predeparture_trajectory_sha256':before.hexdigest(),'schedule_routes_sha256':hashlib.sha256(canonical([contract,routes])).hexdigest(),
            'demand_sha256':digest(output/'demand.rou.xml'),'sumo_version':subprocess.check_output([binary('sumo'),'--version'],text=True).splitlines()[0],
            'command':cmd[1:]}
    (output/'result.json').write_bytes(canonical(result))
    if seed==config['display_seed']:write_gzip(output/'replay.json.gz',{'frames':frames,'ids':ids,'lane_ids':lane_ids,'target':id_lookup[config['target_id']],'series':series,'key':result['key'],'seed':seed})
    print(f'Complete {result["key"]} / {seed}: {accounting["ended"]} trips; target {result["target_trip"]["mean_trip_s"]:.1f}s',flush=True)
    return result

def export(output,config,template):
    vehicles=ET.parse(output/'h10-p100-s42/demand.rou.xml').getroot().findall('vehicle')
    opposite=members(vehicles,config['diagnostic_addendum']);cases=[]
    for tau in config['headways_s']:
        for pace in config['speed_factors']:
            runs=[]
            for seed in config['seeds']:
                folder=output/f'{key(tau,pace)}-s{seed}';r=json.loads((folder/'result.json').read_text())
                trips={v.get('id'):v.attrib for v in ET.parse(folder/'trips.xml').getroot() if v.tag=='tripinfo'}
                if set(trips)!={v.get('id') for v in vehicles}:raise ValueError('Trip membership changed before export')
                for name,group in [('target_trip',[r['target']]),('cohort',members(vehicles,config['cohort'],r['target'])),('others',sorted(i for i in trips if i!=r['target']))]:
                    if trip_metrics(trips,group)!=r[name]:raise ValueError('Trip metrics changed before export: '+name)
                r['opposite_direction']=trip_metrics(trips,opposite);r['opposite_ids_sha256']=hashlib.sha256(canonical(sorted(opposite))).hexdigest()
                r['raw_output_sha256']={name:digest(folder/name) for name in ['trips.xml','fcd.xml.gz','lanechanges.xml','detectors.xml','summary.xml']}
                runs.append(r)
            cases.append({'key':key(tau,pace),'tau':tau,'speedFactor':pace,'runs':runs})
    reference=next(c for c in cases if c['tau']==config['reference']['tau'] and c['speedFactor']==config['reference']['speedFactor'])
    for c in cases:
        for run,ref in zip(c['runs'],reference['runs']):
            for field in ['sumo_version','schedule_routes_sha256','cohort_ids_sha256','opposite_ids_sha256','predeparture_trajectory_sha256','scored_bins']:
                if run[field]!=ref[field]:raise ValueError('Pairing gate failed: '+field+' '+c['key'])
            run['difference']={g:run[g]['mean_trip_s']-ref[g]['mean_trip_s'] for g in ['target_trip','cohort','others','opposite_direction']}
            run['difference']['other_total_s']=run['others']['total_trip_s']-ref['others']['total_trip_s']
    destination=ROOT/'docs/driver-data';destination.mkdir(exist_ok=True)
    import sumolib
    net=sumolib.net.readNet(str(SCENARIO/'network.net.xml'),withInternal=True)
    geometry={k:template[k] for k in ['context_roads','context_labels']}
    geometry['lanes']=[{'id':l.getID(),'shape':l.getShape(),'width':l.getWidth(),'speed':l.getSpeed(),'length_m':l.getLength()} for e in net.getEdges(withInternal=True) for l in e.getLanes()]
    geometry['meta']={'network_sha256':digest(SCENARIO/'network.net.xml')}
    geometry_file=write_gzip(destination/'geometry.json.gz',geometry)
    for c in cases:
        folder=output/f'{c["key"]}-s{config["display_seed"]}'
        replay=json.loads(gzip.decompress((folder/'replay.json.gz').read_bytes()));replay['frames']=replay['frames'][::2];samples={s['t']:s for s in replay['series']}
        with gzip.open(folder/'fcd.xml.gz','rb') as stream:
            for _,elem in ET.iterparse(stream,events=('end',)):
                if elem.tag!='timestep':continue
                t=float(elem.get('time'))
                if t>config['replay_end']:break
                if t in samples:
                    followers=[v.attrib for v in elem if v.get('leaderID')==config['target_id'] and float(v.get('leaderGap'))>=0]
                    f=min(followers,key=lambda x:(float(x['leaderGap']),x['id'])) if followers else None
                    samples[t]['follower']={'id':f['id'],'gap_m':float(f['leaderGap']),'speed':float(f['speed']),'reported_followers':len(followers)} if f else None
                elem.clear()
        c['replay']=write_gzip(destination/(c['key']+'.json.gz'),replay)
    index={'schema':'trafficlab.driver-library.v1','config':config,'config_sha256':digest(CONFIG),'geometry':geometry_file,'reference_key':reference['key'],'cases':cases,
           'source':{k:template['meta'][k] for k in ['source_date','network_sha256','observations_sha256','demand_sha256','source_provenance']},
           'gates':{'matched_inputs':True,'identical_predeparture':True,'all_trips_complete':True,'collision_free':True,'same_diagnostic_mask':True,'empirically_validated':False}}
    (destination/'index.json').write_bytes(canonical(index))
    for name in ['drivers.html','drivers.css','drivers.js','flow-layer.js','driver-view.js']:
        if (ROOT/'viewer'/name).exists():shutil.copyfile(ROOT/'viewer'/name,ROOT/'docs'/name)
    print('Exported 9 recordings and all 27 checked runs.',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,default=ROOT/'runs/merge');p.add_argument('--output',type=Path,default=ROOT/'runs/drivers')
    p.add_argument('--workers',type=int,default=1);p.add_argument('--case');p.add_argument('--seed',type=int);p.add_argument('--export-only',action='store_true');a=p.parse_args()
    config=json.loads(CONFIG.read_text());template=prepare(a.base)
    if not a.export_only:
        jobs=[(h,v,s) for h in config['headways_s'] for v in config['speed_factors'] for s in config['seeds'] if (not a.case or a.case==key(h,v)) and (a.seed is None or a.seed==s)]
        if not jobs:p.error('No configured experiment matches')
        def job(values):
            h,v,s=values;return run_case(a.base.resolve(),a.output.resolve()/f'{key(h,v)}-s{s}',config,template,h,v,s)
        with ThreadPoolExecutor(max_workers=max(1,a.workers)) as pool:list(pool.map(job,jobs))
    if a.export_only or not(a.case or a.seed):export(a.output.resolve(),config,template)
if __name__=='__main__':main()
