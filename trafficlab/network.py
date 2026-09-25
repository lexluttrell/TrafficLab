"""OpenStreetMap adapter. Preserve raw input and conversion provenance."""
import hashlib
import gzip
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import urllib.request
import sumo


def binary(name):
    import os
    return str(Path(sumo.__file__).parent / 'bin' / (name + ('.exe' if os.name == 'nt' else '')))


def build(scenario):
    config = json.loads((scenario / 'scenario.json').read_text())
    source = scenario / 'source.osm.xml'
    if not source.exists() and (scenario / 'source.osm.xml.gz').exists():
        source = scenario / 'source.osm.xml.gz'
    prior = json.loads((scenario / 'provenance.json').read_text()) if (scenario / 'provenance.json').exists() else {}
    retrieved_date = prior.get('retrieved_date_utc', 'unknown')
    if not source.exists():
        with urllib.request.urlopen(config['source_url'], timeout=90) as response:
            data = response.read()
        import xml.etree.ElementTree as ET
        if ET.fromstring(data).tag != 'osm':
            raise ValueError('Source is not OpenStreetMap XML')
        source.write_bytes(data)
        retrieved_date = datetime.now(timezone.utc).date().isoformat()
    output = scenario / 'network.net.xml'
    command = [binary('netconvert'), '--osm-files', str(source),
               '--keep-edges.by-type', 'highway.motorway,highway.motorway_link',
               '--remove-edges.isolated', 'true', '--output.street-names', 'true',
               '--output-file', str(output)]
    result = subprocess.run(command, text=True, capture_output=True)
    (scenario / 'conversion.log').write_text(result.stdout + result.stderr)
    result.check_returncode()
    metadata = {'retrieved_date_utc': retrieved_date, 'source_extent_note': 'OSM returns complete ways intersecting bbox; geometry can extend outside it.', 'source_url': config['source_url'], 'source_sha256': hashlib.sha256(gzip.decompress(source.read_bytes()) if source.suffix == '.gz' else source.read_bytes()).hexdigest(), 'stored_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'network_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'attribution': '© OpenStreetMap contributors, ODbL 1.0',
                'conversion': command[1:], 'sumo_version': subprocess.check_output([binary('sumo'), '--version'], text=True).splitlines()[0]}
    (scenario / 'provenance.json').write_text(json.dumps(metadata, indent=2))
    return output
