"""Scientific-accounting checks; fixtures are fabricated, not empirical validation."""
import unittest

from trafficlab.data.encounters import FT, coverage, deduplicate, find_events, measure_gap


class EncounterMeasurements(unittest.TestCase):
    def test_gap_uses_leader_length_and_exact_time(self):
        follower = dict(id=1,t=100,leader=2,lane=2,y=10,speed=10)
        leader = dict(id=2,t=100,lane=2,y=35,length=5)
        self.assertEqual(measure_gap(follower,{(2,100):leader}), (20,2,None))
        self.assertEqual(measure_gap(follower,{(2,200):leader}), (None,None,"leader_unavailable"))
        leader["lane"]=3
        self.assertEqual(measure_gap(follower,{(2,100):leader})[2],"leader_lane_mismatch")

    def test_stopped_headway_is_missing_and_negative_gap_is_quarantined(self):
        follower=dict(id=1,t=0,leader=2,lane=1,y=10,speed=0)
        leader=dict(id=2,t=0,lane=1,y=20,length=4)
        self.assertEqual(measure_gap(follower,{(2,0):leader}), (6,None,"speed_below_time_gap_threshold"))
        leader["y"]=12
        self.assertEqual(measure_gap(follower,{(2,0):leader}), (None,None,"negative_net_gap"))

    def test_duplicates_collapse_and_conflicts_remove_the_entire_key(self):
        raw=dict(vehicle_id="1",frame_id="1",global_time="100",local_x="5",local_y="10",v_length="12",v_width="6",v_vel="20",v_acc="0",lane_id="2",preceding="0",following="0",v_class="2",space_headway="0",total_frames="3",time_headway="0",location="i-80")
        identical=[dict(raw,source_row_id="a"),dict(raw,source_row_id="b")]
        points,counts=deduplicate(identical,100)
        self.assertEqual(counts["exact_duplicate_rows"],1)
        self.assertAlmostEqual(points[1,0]["speed"],20*FT)
        points,counts=deduplicate(identical+[dict(raw,v_acc="1",source_row_id="c")],100)
        self.assertEqual(points,{})
        self.assertEqual(counts["conflicting_keys"],1)
        with self.assertRaises(ValueError):
            deduplicate([identical[0],identical[0]],100)

    def test_coverage_does_not_bridge_a_missing_frame(self):
        points={(1,t):{"gap_usable":True} for t in range(0,201,100)}
        self.assertTrue(coverage(1,100,.1,points)["continuous"])
        del points[1,100]
        result=coverage(1,100,.1,points)
        self.assertFalse(result["continuous"])
        self.assertEqual(result["present_samples"],2)

    def test_transition_requires_stability_and_prior_repeat_does_not_look_ahead(self):
        points={}
        actors=[]
        followers=[]
        for t in range(0,50001,100):
            lane=1 if t<20000 else 2 if t<30000 else 3
            actor=dict(id=1,t=t,lane=lane,y=100,follower=2,gap=15,gap_usable=True)
            follower=dict(id=2,t=t,lane=lane,y=80,leader=1,follower=0,gap=15,gap_usable=True)
            actors.append(actor);followers.append(follower)
            points[1,t]=actor;points[2,t]=follower
        protocol={"candidate_rules":{"lane_dwell_seconds":2,"mainline_lanes":[1,2,3,4,5,6],"repeated_changes_within_seconds":30}}
        events,_=find_events({1:actors},points,protocol)
        self.assertEqual(len(events),2)
        self.assertTrue(events[0]["repeated_candidate"])
        self.assertFalse(events[0]["prior_repeat"])
        self.assertTrue(events[1]["prior_repeat"])
        self.assertTrue(events[0]["inspectable"])
        actors[205]["lane"]=1  # Lane flicker invalidates both nearby transitions.
        events,_=find_events({1:actors},points,protocol)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["t"],30000)


if __name__=="__main__":
    unittest.main()
