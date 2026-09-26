"""End-to-end completion and merge geometry checks, not field validation."""
import json
import hashlib
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

class MergeCircuit(unittest.TestCase):
    @unittest.skipUnless(Path('runs/merge/replay.json').exists(),'Generate merge run first')
    def test_every_scheduled_vehicle_completes(self):
        replay=json.loads(Path('runs/merge/replay.json').read_text());meta=replay['meta'];r=meta['report'];d=meta['drain_report']
        self.assertEqual(r['scheduled'],14407);self.assertEqual(r['inserted'],r['scheduled'])
        self.assertEqual(r['completed_trips']+r['running'],r['inserted'])
        self.assertEqual(d['completed'],d['scheduled']);self.assertEqual(d['running'],0);self.assertEqual(d['not_inserted'],0)
        self.assertEqual(d['collisions'],0);self.assertEqual(d['teleports'],0)
        for origin in d['origins']:self.assertEqual(origin['completed_after_drain'],origin['scheduled'])
        self.assertTrue(all(n>0 for n in r['ramp_exit_completions'].values()))
        scored=[x for x in replay['comparison']['records'] if x['eligible']]
        self.assertEqual({(x['station_id']) for x in scored},{'401269','400660'});self.assertEqual(len(scored),18)
        self.assertTrue(all(x['end']<=3600 for x in replay['comparison']['records']))
        trips=ET.parse('runs/merge/trips.xml').getroot();self.assertEqual(len(trips),14407)
        self.assertTrue(all(float(t.get('arrival'))>float(t.get('depart')) for t in trips))
        # Demand is unchanged; geometry and path edge IDs are the only route changes.
        current=ET.parse('runs/merge/demand.rou.xml').getroot()
        pairs=[(v.get('id'),v.get('depart')) for v in current.findall('vehicle')]
        original=json.loads(Path('scenarios/pinole-merge/provenance.json').read_text())['original_departure_schedule_sha256']
        self.assertEqual(hashlib.sha256(json.dumps(pairs,separators=(',',':')).encode()).hexdigest(),original)


    def test_merge_lane_connections(self):
        import sumolib
        n=sumolib.net.readNet('scenarios/pinole-merge/network.net.xml')
        for ramp,upstream,downstream in [('1193463511','1193463509#0','1193463509#1'),('7852677','23978795#0','23978795#1')]:
            accel=downstream+'-AddedOnRampEdge';edge=n.getEdge(accel)
            self.assertEqual(edge.getLaneNumber(),5)
            self.assertEqual([c.getToLane().getID() for c in n.getEdge(ramp).getLane(0).getOutgoing()],[accel+'_0'])
            self.assertEqual(len(edge.getLane(0).getOutgoing()),0) # must change lanes before end
            for i in range(4):self.assertEqual([c.getToLane().getID() for c in n.getEdge(upstream).getLane(i).getOutgoing()],[accel+'_'+str(i+1)])
            self.assertTrue(all(c.getState()=='M' for c in n.getEdge(ramp).getLane(0).getOutgoing()))

if __name__=='__main__':unittest.main()
