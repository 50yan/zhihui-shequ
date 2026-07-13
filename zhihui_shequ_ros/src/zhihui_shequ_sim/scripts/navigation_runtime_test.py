#!/usr/bin/env python3
import math
import unittest

import actionlib
import rospy
import rostest
import tf
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseWithCovarianceStamped
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import Image, LaserScan


class NavigationRuntimeTest(unittest.TestCase):
    def test_navigation_stack_topics_tf_and_action_server(self):
        scan = rospy.wait_for_message("/scan", LaserScan, timeout=60.0)
        rospy.wait_for_message("/camera/image_raw", Image, timeout=60.0)
        rospy.wait_for_message("/odom", Odometry, timeout=60.0)
        rospy.wait_for_message("/map", OccupancyGrid, timeout=60.0)
        rospy.wait_for_message("/amcl_pose", PoseWithCovarianceStamped, timeout=60.0)

        self.assertGreaterEqual(scan.angle_max - scan.angle_min, 2.0 * math.pi - 0.02)
        self.assertGreater(len(scan.ranges), 300)

        listener = tf.TransformListener()
        listener.waitForTransform("map", "base_footprint", rospy.Time(0), rospy.Duration(30.0))

        client = actionlib.SimpleActionClient("/move_base", MoveBaseAction)
        self.assertTrue(client.wait_for_server(rospy.Duration(30.0)))

        odom_before = rospy.wait_for_message("/odom", Odometry, timeout=10.0)
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = 3.30
        goal.target_pose.pose.position.y = 3.65
        goal.target_pose.pose.orientation.z = 1.0
        goal.target_pose.pose.orientation.w = 0.0
        client.send_goal(goal)
        self.assertTrue(client.wait_for_result(rospy.Duration(90.0)))
        self.assertEqual(GoalStatus.SUCCEEDED, client.get_state())

        odom_after = rospy.wait_for_message("/odom", Odometry, timeout=10.0)
        dx = odom_after.pose.pose.position.x - odom_before.pose.pose.position.x
        dy = odom_after.pose.pose.position.y - odom_before.pose.pose.position.y
        self.assertGreater(math.hypot(dx, dy), 0.40)


if __name__ == "__main__":
    rospy.init_node("navigation_runtime_test")
    rostest.rosrun("zhihui_shequ_sim", "navigation_runtime_test", NavigationRuntimeTest)
