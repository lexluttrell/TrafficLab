"""Export the merge hypothesis, preserving the original ramp replay."""
from pathlib import Path
import json,gzip,shutil
root=Path(__file__).resolve().parents[1];out=root/'docs'
payload=json.loads((root/'runs/merge/replay.json').read_text())
study=json.loads((out/'ramps-study.json').read_text())
study['runs']=[r for r in study['runs'] if r['key']!='merge']
study['runs'].append({'key':'merge','label':'Acceleration lanes · assumed','report':payload['meta']['report'],
                     'metrics':payload['comparison']['metrics'],'meta':payload['meta'],'comparison':payload['comparison']})
(out/'ramps-study.json').write_text(json.dumps(study,separators=(',',':')))
frames=payload.pop('frames');payload['chunks']=[]
for i in range(0,len(frames),60):
 name=f'merge-frames-{i//60:02}.json.gz';payload['chunks'].append(name)
 (out/name).write_bytes(gzip.compress(json.dumps(frames[i:i+60],separators=(',',':')).encode(),mtime=0))
(out/'merge-replay.json.gz').write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
for name in ['ramps.html','ramps-before.html','ramps.js','app.js','flow-layer.js','style.css','index.html','historical.html']:
 shutil.copyfile(root/'viewer'/name,out/name)
print('Exported merge replay and comparison; original ramp replay retained.')
