"""Rebuild the declared 150 m acceleration-lane hypothesis from frozen OSM."""
from pathlib import Path
import subprocess,json,hashlib,gzip
from trafficlab.network import binary
from trafficlab.data.review import review
root=Path(__file__).resolve().parents[1]
base=root/'scenarios/pinole-ramps';target=root/'scenarios/pinole-merge'
cmd=[binary('netconvert'),'--osm-files',str(base/'source.osm.xml.gz'),
 '--keep-edges.by-type','highway.motorway,highway.motorway_link','--remove-edges.isolated','true',
 '--output.street-names','true','--ramps.set','1193463509#1,23978795#1','--ramps.ramp-length','150',
 '--output-file',str(target/'network.net.xml')]
r=subprocess.run(cmd,capture_output=True,text=True);r.check_returncode();(target/'conversion.log').write_text(r.stdout+r.stderr)
b=review(json.loads(gzip.decompress((base/'observations.json.gz').read_bytes())),target/'network.net.xml')
(target/'observations.json.gz').write_bytes(gzip.compress(json.dumps(b,separators=(',',':')).encode(),mtime=0))
p=json.loads((target/'provenance.json').read_text());p['conversion']=cmd[1:];p['source_network_sha256']=hashlib.sha256((base/'network.net.xml').read_bytes()).hexdigest();p['network_sha256']=hashlib.sha256((target/'network.net.xml').read_bytes()).hexdigest();(target/'provenance.json').write_text(json.dumps(p,indent=2))
print('Built assumed merge geometry and refreshed provisional station mappings.')
