"""Fabricated parser fixtures ONLY. These are not Pinole observations."""
import gzip
import json
from datetime import date
from pathlib import Path
import tempfile
import unittest
from trafficlab.data.pems import normalize

DAY = date(2025, 1, 15)
BBOX = [-122.305, 37.988, -122.27, 38.01]
HEADER = 'ID\tFwy\tDir\tDistrict\tLatitude\tLongitude\tType\tLanes\tName\n'
META = HEADER + '1\t80\tE\t4\t38.0\t-122.29\tML\t4\tFABRICATED TEST STATION\n'
ROW = '01/15/2025 00:00:00,1,4,80,E,ML,0.5,40,100,0,0,60\n'

class PeMSImporter(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.metadata = self.root/'metadata.txt'
        self.obs = self.root/'station_5min.txt'
        self.metadata.write_text(META)
        self.obs.write_text(ROW)
    def tearDown(self):
        self.temp.cleanup()
    def run_import(self, **kwargs):
        return normalize(self.metadata,self.obs,kwargs.get('day',DAY),kwargs.get('metadata_date',DAY),BBOX)
    def test_zero_gap_and_reproducibility(self):
        a = self.run_import()
        self.assertEqual(a,self.run_import())
        self.assertEqual(a['records'][0]['flow_vehicles_per_5min'],0)
        self.assertEqual(a['records'][0]['timestamp_utc'],'2025-01-15T08:00:00+00:00')
        self.assertEqual(len(a['coverage'][0]['missing_intervals']),287)
        self.assertEqual(a['records'][0]['quality_flags'],[])
    def test_missing_invalid_and_partial_preserved(self):
        self.obs.write_text(ROW.replace(',100,0,0,60',',50,0,2,'))
        r=self.run_import()['records'][0]
        self.assertIsNone(r['speed_mph'])
        self.assertIsNone(r['occupancy_fraction'])
        self.assertIn('invalid_occupancy',r['quality_flags'])
        self.assertIn('partially_observed_or_imputed',r['quality_flags'])
        self.assertEqual(r['raw_station_values'][4],'2')
    def test_gzip_sources(self):
        self.obs=self.root/'station_5min.txt.gz'
        self.obs.write_bytes(gzip.compress(ROW.encode()))
        self.assertEqual(len(self.run_import()['records']),1)
    def test_duplicates(self):
        self.obs.write_text(ROW+ROW)
        self.assertEqual(self.run_import()['provenance']['identical_duplicates_removed'],1)
        self.obs.write_text(ROW+ROW.replace(',60',',50'))
        with self.assertRaisesRegex(ValueError,'Conflicting duplicate'):self.run_import()
    def test_future_metadata_and_dst_rejected(self):
        with self.assertRaisesRegex(ValueError,'later'):self.run_import(metadata_date=date(2025,1,16))
        with self.assertRaisesRegex(ValueError,'DST'):self.run_import(day=date(2025,11,2))
    def test_station_mismatch_and_off_grid_rejected(self):
        self.obs.write_text(ROW.replace(',80,E,',',80,W,'))
        with self.assertRaisesRegex(ValueError,'mismatch'):self.run_import()
        self.obs.write_text(ROW.replace('00:00:00','00:01:00'))
        with self.assertRaisesRegex(ValueError,'Off-grid'):self.run_import()
    def test_unselected_stations_and_empty_date(self):
        self.obs.write_text(ROW.replace(',1,4,',',999,4,'))
        with self.assertRaisesRegex(ValueError,'No selected observations'):self.run_import()
    def test_scenario_bounds_and_metadata_duplicates(self):
        self.metadata.write_text(META.replace('38.0','37.0'))
        with self.assertRaisesRegex(ValueError,'No stations'):self.run_import()
        self.metadata.write_text(META+META.splitlines()[1]+'\n')
        with self.assertRaisesRegex(ValueError,'Duplicate selected'):self.run_import()

if __name__=='__main__':unittest.main()
