"""Real SUMO integration checks; these are not empirical traffic validation."""
import tempfile, unittest
from pathlib import Path
from trafficlab.simulation import run
ROOT=Path(__file__).resolve().parents[1]
class Mission001(unittest.TestCase):
    def test_real_run_repeats_and_drains(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=run(ROOT/'scenarios/pinole',Path(tmp)/'a',42)
            b=run(ROOT/'scenarios/pinole',Path(tmp)/'b',42)
            self.assertEqual(a['frames'],b['frames'])
            report=a['meta']['report']
            self.assertEqual(report['completed_trips'],600)
            self.assertEqual(report['inserted'],report['completed_trips'])
            for field in ['running','waiting','teleports','collisions']:self.assertEqual(report[field],0)
            self.assertEqual(len(a['meta']['routes']),2)
            self.assertTrue(all(r['length_m']>3000 for r in a['meta']['routes']))
            self.assertGreater(len(a['context_roads']),0)
            positions={}
            for frame in a['frames']:
                for vehicle in frame['vehicles']:
                    positions.setdefault(vehicle[0],set()).add(tuple(vehicle[1:3]))
            self.assertEqual(len(positions),600)
            self.assertTrue(all(len(p)>1 for p in positions.values()))
if __name__=='__main__':unittest.main()
