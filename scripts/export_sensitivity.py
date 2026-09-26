"""Publish complete predefined cases; refuse mismatched scoring or demand."""
import json
import gzip
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
cases=[json.loads((ROOT/f'runs/sensitivity/l{length}-s{seed}/result.json').read_text()) for length in [100,150,200] for seed in [42,43]]
mask=cases[0]['eligible_station_bins']
assert len(mask)==18 and {p[0] for p in mask}=={'401269','400660'},'Unexpected scoring population'
for c in cases:
    assert c['eligible_station_bins']==mask,'Scoring mask differs between cases'
    r,d=c['report'],c['drain']
    assert r['inserted']==r['completed_trips']+r['running'],'Cutoff accounting failure'
    assert d['inserted']==d['completed']+d['running'],'Drain accounting failure'
    assert sum(o['scheduled'] for o in c['origins'])==r['scheduled'],'Origin accounting failure'
for seed in [42,43]:
    assert len({c['departure_schedule_sha256'] for c in cases if c['seed']==seed})==1,'Geometry changed departure schedules'
    assert len({c['report']['scheduled'] for c in cases if c['seed']==seed})==1
study={'design':{'length_settings_m':[100,150,200],'seeds':[42,43],
 'date':'2026-09-24','input_window':'07:30–08:30 source-local','drain_seconds':900,
 'scope':'Same-day geometry sensitivity with two random seeds; not confidence intervals or held-out validation.',
 'constants':'Same five-minute source counts, exit fractions and driver parameters. Within each seed, identical departure IDs/times across lengths.',
 'seed_effect':'Seed changes within-bin departure times, exit assignment and simulated driver randomness.',
 'replay_note':'Replay remains the 150 m / seed 42 case. Selecting a result changes diagnostics only.'},'cases':cases,
 'origin_names':{s['id']:s['direction']+' · '+s['name'] for s in json.loads(gzip.decompress((ROOT/'scenarios/pinole-ramps/observations.json.gz').read_bytes()))['stations']}}
(ROOT/'docs/merge-sensitivity.json').write_text(json.dumps(study,separators=(',',':')))
for name in ['ramps.html','sensitivity.js','style.css']:
    shutil.copyfile(ROOT/'viewer'/name,ROOT/'docs'/name)
print('Exported six-case study after demand, scoring-mask and trip-accounting gates.')
