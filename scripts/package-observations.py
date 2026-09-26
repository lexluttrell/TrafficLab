"""Build a self-contained local HTML inspector, without publishing source data."""
import argparse
from pathlib import Path
import json

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--input',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[1]
data=json.loads(a.input.read_text())
html=(root/'viewer/observations.html').read_text()
html=html.replace('<link rel="stylesheet" href="observations.css">','<style>'+(root/'viewer/observations.css').read_text()+'</style>')
encoded=json.dumps(data,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
html=html.replace('<script src="observations.js"></script>','<script id="embedded-observations" type="application/json">'+encoded+'</script><script>'+(root/'viewer/observations.js').read_text()+'</script>')
html=html.replace('href="index.html"','href="https://lexluttrell.github.io/TrafficLab/"')
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(html)
print(a.output)
