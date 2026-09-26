"""Export actual SUMO states, not browser-generated motion."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from .network import binary
from .demand import build
from .context import roads

def run(scenario,output,seed=None):
    output.mkdir(parents=True,exist_ok=True)
    config=json.loads((scenario/'scenario.json').read_text())
    seed=config['seed'] if seed is None else seed
    network=scenario/'network.net.xml'
    net,routes=build(network,output/'demand.rou.xml',config)
    cmd=[binary('sumo'),'-n',str(network),'-r',str(output/'demand.rou.xml'),'--seed',str(seed),'--step-length','0.2','--end',str(config['demand_end']+600),'--fcd-output',str(output/'fcd.xml'),'--device.fcd.period','1','--fcd-output.acceleration','true','--tripinfo-output',str(output/'trips.xml'),'--summary-output',str(output/'summary.xml'),'--no-step-log','true','--log',str(output/'sumo.log')]
    subprocess.run(cmd,check=True)
    frames=[]
    for _,e in ET.iterparse(output/'fcd.xml',events=('end',)):
        if e.tag=='timestep':
            vehicles=[[v.attrib['id'],float(v.attrib['x']),float(v.attrib['y']),float(v.attrib['speed']),float(v.attrib['angle']),v.attrib['lane'],float(v.attrib['pos']),float(v.attrib.get('acceleration',0))] for v in e]
            frames.append({'time':float(e.attrib['time']),'vehicles':vehicles});e.clear()
    while len(frames)>1 and not frames[-1]['vehicles'] and not frames[-2]['vehicles']:frames.pop()
    lanes=[{'id':l.getID(),'shape':l.getShape(),'width':l.getWidth(),'name':e.getName(),'speed':l.getSpeed()} for e in net.getEdges() for l in e.getLanes()]
    trips=ET.parse(output/'trips.xml').getroot();last=ET.parse(output/'summary.xml').getroot()[-1].attrib
    report={'completed_trips':len(trips),**{k:int(last.get(k,0)) for k in ['inserted','running','waiting','teleports','collisions']}}
    metadata={'scenario':config['name'],'seed':seed,'scientific_status':'Synthetic demand · uncalibrated','sumo_version':subprocess.check_output([binary('sumo'),'--version'],text=True).splitlines()[0],'network_sha256':hashlib.sha256(network.read_bytes()).hexdigest(),'demand_sha256':hashlib.sha256((output/'demand.rou.xml').read_bytes()).hexdigest(),'routes':routes,'report':report,'command':cmd[1:],'vehicle_columns':['id','x_m','y_m','speed_m_s','angle_deg','lane','lane_position_m','acceleration_m_s2']}
    payload={'meta':metadata,'lanes':lanes,'frames':frames,'context_labels':config.get('context_labels',[]),'context_roads':roads(scenario/'source.osm.xml',net)}
    (output/'replay.json').write_text(json.dumps(payload,separators=(',',':')))
    (output/'manifest.json').write_text(json.dumps(metadata,indent=2))
    for file in (Path(__file__).resolve().parents[1]/'viewer').iterdir():
        if file.is_file():shutil.copy(file,output/file.name)
    viewer=Path(__file__).resolve().parents[1]/'viewer'
    html=(viewer/'index.html').read_text()
    html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(viewer/'style.css').read_text()+'</style>')
    html=html.replace('<script src="flow-layer.js"></script>','<script>'+(viewer/'flow-layer.js').read_text()+'</script>')
    embedded=json.dumps(payload,separators=(',',':')).replace('<', '\\u003c')
    html=html.replace('<script src="app.js"></script>','<script id="embedded-replay" type="application/json">'+embedded+'</script><script>'+(viewer/'app.js').read_text()+'</script>')
    (output/'Open-TrafficLab.html').write_text(html,encoding='utf-8')
    print(json.dumps(report,indent=2));return payload
