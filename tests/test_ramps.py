"""Accounting and topology gates for ramp demand, not empirical validation."""
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from trafficlab.ramp_demand import estimate_fraction, connected

class RampDemand(unittest.TestCase):
    def test_fraction_boundaries(self):
        self.assertEqual(estimate_fraction(100,20,90),(.25,.25))
        self.assertEqual(estimate_fraction(100,0,110),(0,-.1))
        self.assertEqual(estimate_fraction(100,0,0),(.8,1))
        with self.assertRaises(ValueError):estimate_fraction(0,0,0)

    @unittest.skipUnless(Path('runs/ramps/final-central/replay.json').exists(),'Generate ramp study first')
    def test_real_run_accounting_and_comparable_control(self):
        import sumolib
        net=sumolib.net.readNet('scenarios/pinole-ramps/network.net.xml')
        loaded={}
        for key in ['central','control','low','high']:
            root=Path('runs/ramps/final-'+key)
            replay=json.loads((root/'replay.json').read_text());report=replay['meta']['report']
            self.assertEqual(report['inserted'],report['completed_trips']+report['running'])
            self.assertEqual(report['scheduled'],report['inserted']+report['not_inserted'])
            self.assertEqual(report['inserted'],sum(o['inserted'] for o in report['origins']))
            self.assertEqual(report['collisions'],0);self.assertEqual(report['teleports'],0)
            eligible=[r for r in replay['comparison']['records'] if r['eligible']]
            self.assertEqual({r['station_id'] for r in eligible},{'401269','400660'})
            self.assertEqual(len(eligible),18)
            doc=ET.parse(root/'demand.rou.xml').getroot()
            for route in doc.findall('route'):connected(net,route.attrib['edges'].split())
            vehicles=doc.findall('vehicle')
            self.assertEqual(len({v.attrib['id'] for v in vehicles}),len(vehicles))
            loaded[key]={v.attrib['id']:v.attrib['depart'] for v in vehicles if v.attrib['id'].startswith(('o400430-','o401084-'))}
            if key!='control':
                self.assertGreater(report['ramp_origin_completed'],0)
                self.assertTrue(all(n>0 for n in report['ramp_exit_completions'].values()))
                self.assertTrue(all(t['clipped']==0 for t in replay['meta']['ramp_plan']['exit_targets']))
        self.assertTrue(all(v==loaded['control'] for v in loaded.values()))

if __name__=='__main__':unittest.main()
