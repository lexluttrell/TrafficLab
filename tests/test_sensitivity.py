"""Gates for the published six-case experiment, not empirical validation."""
import json
from pathlib import Path
import unittest
from scripts.merge_sensitivity import percentile

class Sensitivity(unittest.TestCase):
    def test_percentile_handles_small_groups(self):
        self.assertIsNone(percentile([],.95))
        self.assertEqual(percentile([7],.95),7)
        self.assertEqual(percentile([0,100],.95),95)

    @unittest.skipUnless(Path('docs/merge-sensitivity.json').exists(),'Export study first')
    def test_predeclared_cases_remain_comparable(self):
        cases=json.loads(Path('docs/merge-sensitivity.json').read_text())['cases']
        self.assertEqual({(c['length_setting_m'],c['seed']) for c in cases},{(l,s) for l in [100,150,200] for s in [42,43]})
        self.assertEqual(len(cases),6)
        mask=cases[0]['eligible_station_bins']
        self.assertEqual(len(mask),18)
        for c in cases:
            self.assertEqual(c['eligible_station_bins'],mask)
            self.assertEqual(c['report']['scheduled'],14407)
            d=c['drain'];self.assertEqual(d['inserted'],d['completed']+d['running'])
            self.assertEqual(d['scheduled'],d['inserted']+d['not_inserted'])
            self.assertEqual(sum(o['completed_after_drain'] for o in c['origins']),d['completed'])
            self.assertTrue(all(o['p95_time_s']>=0 for o in c['origins']))
        for seed in [42,43]:self.assertEqual(len({c['departure_schedule_sha256'] for c in cases if c['seed']==seed}),1)
        self.assertEqual(len({c['source_aggregate_sha256'] for c in cases}),1)
        self.assertEqual(len({c['source_osm_gzip_sha256'] for c in cases}),1)

if __name__=='__main__':unittest.main()
