"""Scientific accounting checks with fabricated values, not traffic validation."""
import random
import unittest
from trafficlab.comparison import aggregate_lanes, diagnostics, MPH_PER_MPS
from trafficlab.historical import build_departures

class Comparison(unittest.TestCase):
    def test_detector_aggregation_uses_vehicle_counts_not_lane_mean(self):
        rows=[{'nVehContrib':'3','speed':'10','occupancy':'20'},
              {'nVehContrib':'1','speed':'30','occupancy':'40'},
              {'nVehContrib':'0','speed':'-1','occupancy':'0'}]
        result=aggregate_lanes(rows)
        self.assertEqual(result['count'],4)
        self.assertAlmostEqual(result['speed_mph'],15*MPH_PER_MPS)
        self.assertAlmostEqual(result['occupancy_fraction'],.2)
        empty=aggregate_lanes([{'nVehContrib':'0','speed':'-1','occupancy':'0'}])
        self.assertEqual(empty['count'],0)
        self.assertIsNone(empty['speed_mph'])

    def test_exclusion_and_missing_values_do_not_improve_score(self):
        rows=[{'eligible':True,'simulated':{'count':12,'speed_mph':None},'observed':{'count':10,'speed_mph':40}},
              {'eligible':False,'simulated':{'count':1000,'speed_mph':100},'observed':{'count':0,'speed_mph':0}}]
        score=diagnostics(rows)
        self.assertEqual(score['count']['mae'],2)
        self.assertEqual(score['count']['wape_percent'],20)
        self.assertEqual(score['speed_mph']['bins'],0)
        self.assertIsNone(score['speed_mph']['mae'])

    def test_input_counts_and_bin_boundaries_preserved(self):
        a=build_departures(101,300,random.Random(42))
        self.assertEqual(a,build_departures(101,300,random.Random(42)))
        self.assertEqual(len(a),101)
        self.assertTrue(all(300<=t<600 for t in a))
        self.assertEqual(build_departures(0,0,random.Random(42)),[])
        with self.assertRaises(ValueError):build_departures(None,0,random.Random(42))
        with self.assertRaises(ValueError):build_departures(-1,0,random.Random(42))

if __name__=='__main__':unittest.main()
