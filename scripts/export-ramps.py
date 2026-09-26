"""Export the central ramp replay and all four auditable scenario summaries."""
import gzip
import json
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
out=root/'docs'
bundle_path=root/'runs/ramps/reviewed.json'
if bundle_path.exists():bundle=json.loads(bundle_path.read_text())
else:bundle=json.loads(gzip.decompress((root/'scenarios/pinole-ramps/observations.json.gz').read_bytes()))
# Publish aggregate five-minute records only, never redundant raw lane strings.
for row in bundle['records']:
    row.pop('raw_station_values',None)
    row.pop('raw_lane_values',None)
normalized=root/'scenarios/pinole-ramps/observations.json.gz'
normalized.write_bytes(gzip.compress(json.dumps(bundle,separators=(',',':')).encode(),mtime=0))
study={'runs':[],'names':{s['id']:s['name'] for s in bundle['stations']}}
for key,label in [('control','Through-only control'),('central','Ramps · central'),('low','Ramps · low exits'),('high','Ramps · high exits')]:
    payload=json.loads((root/f'runs/ramps/final-{key}/replay.json').read_text())
    study['runs'].append({'key':key,'label':label,'report':payload['meta']['report'],'metrics':payload['comparison']['metrics'],
                         'meta':payload['meta'],'comparison':payload['comparison']})
    if key=='central':central=payload
study['exits']=[]
for event in central['meta']['ramp_plan']['bindings']:
    if event['kind']!='exit':continue
    estimate=next((e for e in central['meta']['ramp_plan']['estimates'] if e['station']==event['station']),None)
    study['exits'].append({'station':event['station'],'name':study['names'][event['station']],
        'status':'Inferred hour-total balance' if estimate else 'Reported PeMS count',
        'fraction':estimate['applied_fraction'] if estimate else None,
        'count':sum(t['assigned'] for t in central['meta']['ramp_plan']['exit_targets'] if t['station_id']==event['station'])})
(out/'ramps-study.json').write_text(json.dumps(study,separators=(',',':')))
frames=central.pop('frames');central['chunks']=[]
for i in range(0,len(frames),60):
    name=f'ramps-frames-{i//60:02}.json.gz';central['chunks'].append(name)
    (out/name).write_bytes(gzip.compress(json.dumps(frames[i:i+60],separators=(',',':')).encode(),mtime=0))
(out/'ramps-replay.json.gz').write_bytes(gzip.compress(json.dumps(central,separators=(',',':')).encode(),mtime=0))
for name in ['ramps.html','ramps.js','app.js','style.css','index.html','historical.html']:
    shutil.copyfile(root/'viewer'/name,out/name)
source=root/'scenarios/pinole-ramps/source.osm.xml'
if source.exists():source.with_suffix('.xml.gz').write_bytes(gzip.compress(source.read_bytes(),mtime=0))
print('Exported central replay, four scenario diagnostics and aggregate observation bundle.')
