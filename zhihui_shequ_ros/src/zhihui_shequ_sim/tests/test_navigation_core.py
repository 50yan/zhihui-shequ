#!/usr/bin/env python3
import math
import os
import sys
import tempfile
import unittest


SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from navigation_core import (
    choose_avoidance_turn,
    data_is_fresh,
    next_numbered_directory,
    patrol_result,
    waypoint_command,
)


class NavigationCoreTest(unittest.TestCase):
    def test_waypoint_command_turns_then_drives_to_goal(self):
        linear, angular, reached = waypoint_command(
            current_x=0.0,
            current_y=0.0,
            current_yaw=math.pi / 2.0,
            target_x=2.0,
            target_y=0.0,
            max_linear=0.6,
            max_angular=1.0,
            distance_tolerance=0.15,
        )
        self.assertFalse(reached)
        self.assertEqual(0.0, linear)
        self.assertLess(angular, 0.0)

        linear, angular, reached = waypoint_command(
            current_x=0.0,
            current_y=0.0,
            current_yaw=0.0,
            target_x=2.0,
            target_y=0.0,
            max_linear=0.6,
            max_angular=1.0,
            distance_tolerance=0.15,
        )
        self.assertFalse(reached)
        self.assertGreater(linear, 0.0)
        self.assertAlmostEqual(0.0, angular)

    def test_waypoint_command_stops_inside_tolerance(self):
        self.assertEqual(
            (0.0, 0.0, True),
            waypoint_command(0.0, 0.0, 0.0, 0.05, 0.04, 0.6, 1.0, 0.15),
        )

    def test_avoidance_turn_selects_side_with_more_clearance(self):
        self.assertGreater(choose_avoidance_turn(left_clearance=2.0, right_clearance=0.8, speed=0.7), 0.0)
        self.assertLess(choose_avoidance_turn(left_clearance=0.5, right_clearance=1.5, speed=0.7), 0.0)

    def test_numbered_output_directories_increment_per_run(self):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "1"))
            os.mkdir(os.path.join(root, "3"))
            os.mkdir(os.path.join(root, "notes"))
            self.assertEqual(os.path.join(root, "4"), next_numbered_directory(root))

    def test_stale_sensor_data_is_rejected(self):
        self.assertTrue(data_is_fresh(last_time=9.5, now=10.0, timeout=1.0))
        self.assertFalse(data_is_fresh(last_time=8.0, now=10.0, timeout=1.0))
        self.assertFalse(data_is_fresh(last_time=None, now=10.0, timeout=1.0))

    def test_patrol_reports_incomplete_when_any_goal_fails(self):
        terminal, status = patrol_result(
            total=5,
            succeeded=4,
            failed=1,
            captures=2,
            expected_captures=3,
        )
        self.assertEqual("incomplete", terminal)
        self.assertIn("failed=1", status)

        terminal, status = patrol_result(
            total=5,
            succeeded=5,
            failed=0,
            captures=3,
            expected_captures=3,
        )
        self.assertEqual("finished", terminal)
        self.assertIn("captures=3/3", status)

        terminal, status = patrol_result(
            total=5,
            succeeded=5,
            failed=0,
            captures=2,
            expected_captures=3,
        )
        self.assertEqual("incomplete", terminal)
        self.assertIn("captures=2/3", status)


if __name__ == "__main__":
    unittest.main()
