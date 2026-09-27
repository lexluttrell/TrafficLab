"""Experiment accounting and reproducibility gates, not empirical validation."""
import gzip,hashlib,json,unittest
from pathlib import Path
from trafficlab.driver_experiment import trip_metrics
ROOT=Path(__file__).resolve().parents[1]
class DriverExperiments(unittest.TestCase):
 def test_insertion_delay_and_incomplete_trips(self):
  trips={'a':{'arrival':'30','duration':'20','departDelay':'5','waitingTime':'2'}}
  self.assertEqual(trip_metrics(trips,['a'])['mean_trip_s'],25)
  with self.assertRaises(ValueError):trip_metrics(trips,['a','missing'])
  trips['a']['arrival']='-1'
  with self.assertRaises(ValueError):trip_metrics(trips,['a'])
  with self.assertRaises(ValueError):trip_metrics({},[])
 @unittest.skipUnless((ROOT/'docs/driver-data/index.json').exists(),'Generate library first')
 def test_published_library_has_real_matched_runs(self):
  folder=ROOT/'docs/driver-data';index=json.loads((folder/'index.json').read_text());cases=index['cases'];reference=next(c for c in cases if c['key']==index['reference_key'])
  self.assertEqual(len(cases),9);self.assertEqual({(c['tau'],c['speedFactor']) for c in cases},{(h,p) for h in [1,1.5,2] for p in [.9,1,1.1]})
  for c in cases:
   self.assertEqual([r['seed'] for r in c['runs']],[42,43,44])
   for r,b in zip(c['runs'],reference['runs']):
    for field in ['sumo_version','schedule_routes_sha256','cohort_ids_sha256','opposite_ids_sha256','predeparture_trajectory_sha256','scored_bins']:self.assertEqual(r[field],b[field])
    self.assertEqual(len(r['scored_bins']),18);self.assertEqual({x[0] for x in r['scored_bins']},{'401269','400660'})
    self.assertEqual(r['accounting']['scheduled'],14407);self.assertEqual(r['accounting']['ended'],14407);self.assertEqual(r['others']['n'],14406);self.assertEqual(r['cohort']['n'],106);self.assertEqual(r['opposite_direction']['n'],173)
    for f in ['running','waiting','collisions','teleports']:self.assertEqual(r['accounting'][f],0)
    for g in ['target_trip','cohort','others','opposite_direction']:self.assertAlmostEqual(r['difference'][g],r[g]['mean_trip_s']-b[g]['mean_trip_s'])
    self.assertEqual(r['diagnostics']['eligible_bins'],18)
   raw=(folder/c['replay']['file']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),c['replay']['sha256']);movie=json.loads(gzip.decompress(raw));self.assertEqual(movie['seed'],42);self.assertEqual(movie['ids'][movie['target']],index['config']['target_id'])
   positions=[tuple(v[1:3]) for f in movie['frames'] for v in f['cars'] if v[0]==movie['target']];self.assertGreater(len(set(positions)),50)
   self.assertTrue(all(f['t']<=index['config']['replay_end'] for f in movie['frames']));self.assertTrue(any(s['follower'] for s in movie['series']))
   self.assertTrue(all(s['gap_m'] is None or s['gap_m']>=0 for s in movie['series']))
   for s in movie['series']:
    if s['speed']<2:self.assertIsNone(s['time_gap_s'])
    elif s['gap_m'] is not None:self.assertAlmostEqual(s['time_gap_s'],s['gap_m']/s['speed'])
  self.assertTrue(all(r['difference']['target_trip']==0 for r in reference['runs']));self.assertFalse(index['gates']['empirically_validated'])
 @unittest.skipUnless((ROOT/'runs/drivers-repeat/h10-p100-s42/result.json').exists(),'Run independent reference repeat')
 def test_actual_sumo_repeat(self):
  a=ROOT/'runs/drivers/h10-p100-s42';b=ROOT/'runs/drivers-repeat/h10-p100-s42';x=json.loads((a/'result.json').read_text());y=json.loads((b/'result.json').read_text());x.pop('command');y.pop('command');self.assertEqual(x,y);self.assertEqual((a/'replay.json.gz').read_bytes(),(b/'replay.json.gz').read_bytes())
if __name__=='__main__':unittest.main()
