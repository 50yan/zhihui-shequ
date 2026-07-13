#!/usr/bin/env python3
import math
import os
import sys
import time

import actionlib
import cv2
import rospy
import yaml
from actionlib_msgs.msg import GoalStatus
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseWithCovarianceStamped, Quaternion
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from sensor_msgs.msg import Image
from std_msgs.msg import String

script_dir = os.path.dirname(os.path.abspath(globals().get("__file__", globals().get("python_script", sys.argv[0]))))
sys.path.insert(0, script_dir)
from navigation_core import next_numbered_directory, patrol_result


def quaternion_from_yaw(yaw):
    return Quaternion(0.0, 0.0, math.sin(float(yaw) * 0.5), math.cos(float(yaw) * 0.5))


class PatrolNavigation:
    def __init__(self):
        config_path = rospy.get_param("~config")
        with open(config_path, "r", encoding="utf-8") as stream:
            self.config = yaml.safe_load(stream)

        output_root = self.config.get("output_dir", "~/camera")
        self.output_dir = next_numbered_directory(output_root)
        os.makedirs(self.output_dir, exist_ok=False)

        self.bridge = CvBridge()
        self.last_image = None
        self.amcl_pose = None
        self.status_pub = rospy.Publisher("/zhihui_shequ/navigation_status", String, queue_size=10, latch=True)
        self.goal_pub = rospy.Publisher("/zhihui_shequ/current_goal", String, queue_size=10, latch=True)
        self.capture_pub = rospy.Publisher("/zhihui_shequ/last_capture", String, queue_size=10, latch=True)

        camera_topic = self.config.get("camera_topic", "/camera/image_raw")
        rospy.Subscriber(camera_topic, Image, self._on_image, queue_size=1)
        rospy.Subscriber("/amcl_pose", PoseWithCovarianceStamped, self._on_amcl_pose, queue_size=1)

        action_name = self.config.get("move_base_action", "/move_base")
        self.client = actionlib.SimpleActionClient(action_name, MoveBaseAction)
        self._set_status("waiting for move_base")
        server_wait = float(self.config.get("server_wait", 60.0))
        if not self.client.wait_for_server(rospy.Duration(server_wait)):
            raise RuntimeError("move_base action server unavailable after %.1f seconds" % server_wait)
        rospy.loginfo("Patrol output directory: %s", self.output_dir)

    def _on_image(self, msg):
        try:
            self.last_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            rospy.logwarn("Patrol camera conversion failed: %s", exc)

    def _on_amcl_pose(self, msg):
        self.amcl_pose = msg.pose.pose

    def _set_status(self, text):
        self.status_pub.publish(String(data=str(text)))
        rospy.loginfo("Navigation status: %s", text)

    def _goal_message(self, waypoint):
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = self.config.get("goal_frame", "map")
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = float(waypoint["x"])
        goal.target_pose.pose.position.y = float(waypoint["y"])
        goal.target_pose.pose.orientation = quaternion_from_yaw(waypoint.get("yaw", 0.0))
        return goal

    def _wait_for_camera(self):
        deadline = time.time() + float(self.config.get("capture_camera_wait", 3.0))
        while self.last_image is None and time.time() < deadline and not rospy.is_shutdown():
            rospy.sleep(0.1)
        return self.last_image is not None

    def capture(self, label):
        rospy.sleep(float(self.config.get("settle_time", 0.8)))
        if not self._wait_for_camera():
            rospy.logwarn("No camera image available for capture %s", label)
            return None

        image = self.last_image.copy()
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        raw_path = os.path.join(self.output_dir, "%s_%s.jpg" % (timestamp, label))
        if not cv2.imwrite(raw_path, image):
            rospy.logerr("Failed to save capture image: %s", raw_path)
            return None

        message = "%s: %s" % (label, raw_path)
        self.capture_pub.publish(String(data=message))
        rospy.loginfo("Capture saved: %s", message)
        return raw_path

    def run(self):
        localization_wait = float(self.config.get("localization_wait", 5.0))
        self._set_status("waiting for AMCL localization")
        deadline = time.time() + localization_wait
        while self.amcl_pose is None and time.time() < deadline and not rospy.is_shutdown():
            rospy.sleep(0.1)
        if self.amcl_pose is None:
            message = "AMCL localization unavailable after %.1f seconds" % localization_wait
            rospy.logerr(message)
            if bool(self.config.get("require_localization", True)):
                self.goal_pub.publish(String(data="aborted"))
                self._set_status("patrol aborted: " + message)
                return
        else:
            rospy.sleep(float(self.config.get("localization_settle_time", 2.0)))

        goal_timeout = float(self.config.get("goal_timeout", 120.0))
        continue_on_failure = bool(self.config.get("continue_on_failure", True))
        waypoints = self.config.get("waypoints", [])
        expected_captures = sum(1 for waypoint in waypoints if waypoint.get("capture"))
        succeeded = 0
        failed = 0
        captures = 0
        for waypoint in waypoints:
            if rospy.is_shutdown():
                break
            name = waypoint.get("name", "unnamed")
            self.goal_pub.publish(String(data=name))
            self._set_status("navigating to %s" % name)
            self.client.send_goal(self._goal_message(waypoint))
            finished = self.client.wait_for_result(rospy.Duration(goal_timeout))
            if not finished:
                self.client.cancel_goal()
                self._set_status("goal timeout: %s" % name)
                failed += 1
                if not continue_on_failure:
                    break
                continue

            state = self.client.get_state()
            if state != GoalStatus.SUCCEEDED:
                self._set_status("goal failed: %s state=%d" % (name, state))
                failed += 1
                if not continue_on_failure:
                    break
                continue

            succeeded += 1
            self._set_status("arrived at %s" % name)
            label = waypoint.get("capture")
            if label and self.capture(label):
                captures += 1

        terminal_goal, status = patrol_result(
            len(waypoints),
            succeeded,
            failed,
            captures,
            expected_captures,
        )
        self.goal_pub.publish(String(data=terminal_goal))
        self._set_status(status)


def main():
    rospy.init_node("patrol_navigation")
    PatrolNavigation().run()


if __name__ == "__main__":
    main()
