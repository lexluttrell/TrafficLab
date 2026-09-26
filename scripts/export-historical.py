"""Publish a separately named historical baseline without replacing Mission 001."""
import argparse
import gzip
import json
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,default=Path('runs/historical'))
p.add_argument('--destination',type=Path,default=Path('docs'))
a=p.parse_args();root=Path(__file__).resolve().parents[1]
d=json.loads((a.source/'replay.json').read_text());frames=d.pop('frames');d['chunks']=[]
a.destination.mkdir(parents=True,exist_ok=True)
for i in range(0,len(frames),60):
 name=f'historical-frames-{i//60:02}.json.gz';d['chunks'].append(name)
 (a.destination/name).write_bytes(gzip.compress(json.dumps(frames[i:i+60],separators=(',',':')).encode(),mtime=0))
(a.destination/'historical-replay.json.gz').write_bytes(gzip.compress(json.dumps(d,separators=(',',':')).encode(),mtime=0))
for name in ['historical.html','app.js','style.css','index.html']:
 shutil.copyfile(root/'viewer'/name,a.destination/name)
print('Exported historical replay, preserving the original replay bundle.')
