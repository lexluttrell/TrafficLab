import argparse
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from .network import build
from .simulation import run
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description='TrafficLab Mission 001')
    p.add_argument('command',choices=['build','run','serve','demo'])
    p.add_argument('--scenario',type=Path,default=ROOT/'scenarios'/'pinole')
    p.add_argument('--output',type=Path,default=ROOT/'runs'/'pinole')
    p.add_argument('--seed',type=int);p.add_argument('--port',type=int,default=8765)
    a=p.parse_args();s=a.scenario.resolve();o=a.output.resolve()
    if a.command=='build':build(s)
    if a.command in ('run','demo'):
        if not (s/'network.net.xml').exists():build(s)
        run(s,o,a.seed)
    if a.command in ('serve','demo'):
        if not (o/'replay.json').exists():p.error('Run first: python -m trafficlab run')
        print(f'Open http://localhost:{a.port} — Ctrl+C to stop',flush=True)
        server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(SimpleHTTPRequestHandler,directory=str(o)))
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()
if __name__=='__main__':main()
