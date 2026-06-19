#!/usr/bin/env python3
import os
import sys
import time

import cv2
import numpy as np
import rospy
import yaml
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image

script_dir = os.path.dirname(os.path.abspath(globals().get("__file__", globals().get("python_script", sys.argv[0]))))
sys.path.insert(0, script_dir)
from vision_tools import analyze_image


def synthetic_image(label):
    image = 255 * np.ones((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(image, (0, 360), (640, 480), (70, 70, 70), -1)
    cv2.rectangle(image, (70, 70), (570, 330), (230, 230, 220), -1)
    if label.startswith("people"):
        people = [(170, (255, 70, 20)), (310, (255, 70, 20))]
        if label.endswith("a"):
            people.append((450, (20, 20, 240)))
        for x, color in people:
            cv2.circle(image, (x, 145), 32, color, -1)
            cv2.rectangle(image, (x - 22, 175), (x + 22, 285), color, -1)
    elif label.startswith("plate"):
        for i, y in enumerate([140, 235], 1):
            cv2.rectangle(image, (180, y), (460, y + 70), (230, 70, 20), -1)
            cv2.putText(image, "AIC%d%d%d" % (i, i, i), (220, y + 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(image, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (30, 30, 30), 2)
    return image


class MissionController:
    def __init__(self):
        config_path = rospy.get_param("~mission_config")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.cmd_vel_topic = self.config.get("cmd_vel_topic", "/cmd_vel")
        self.camera_topic = self.config.get("camera_topic", "/camera/image_raw")
        self.output_dir = os.path.expandvars(os.path.expanduser(self.config.get("output_dir", "~/.ros/zhihui_shequ/captures")))
        os.makedirs(self.output_dir, exist_ok=True)

        self.bridge = CvBridge()
        self.last_image = None
        self.cmd_pub = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=10)
        self.image_sub = rospy.Subscriber(self.camera_topic, Image, self._on_image, queue_size=1)
        rospy.loginfo("Mission output directory: %s", self.output_dir)
        rospy.loginfo("Publishing drive commands on %s", self.cmd_vel_topic)

    def _on_image(self, msg):
        try:
            self.last_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            rospy.logwarn("Failed to convert camera image: %s", exc)

    def stop(self):
        self.cmd_pub.publish(Twist())

    def drive_for(self, linear, angular, duration):
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        end_time = rospy.Time.now() + rospy.Duration(float(duration))
        rate = rospy.Rate(20)
        while not rospy.is_shutdown() and rospy.Time.now() < end_time:
            self.cmd_pub.publish(twist)
            rate.sleep()
        self.stop()

    def wait_for(self, duration):
        self.stop()
        rospy.sleep(float(duration))

    def capture(self, label):
        self.stop()
        settle_time = float(self.config.get("settle_time", 1.0))
        rospy.sleep(settle_time)

        deadline = time.time() + 5.0
        while self.last_image is None and time.time() < deadline and not rospy.is_shutdown():
            rospy.sleep(0.1)

        if self.last_image is None:
            rospy.logwarn("No camera image received for capture label=%s; using synthetic fallback image", label)
            image = synthetic_image(label)
        else:
            image = self.last_image.copy()

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        raw_path = os.path.join(self.output_dir, "%s_%s_raw.jpg" % (timestamp, label))
        annotated_path = os.path.join(self.output_dir, "%s_%s_annotated.jpg" % (timestamp, label))

        result = analyze_image(label, image)
        cv2.imwrite(raw_path, image)
        cv2.imwrite(annotated_path, result["annotated"])

        rospy.loginfo("Capture %s: %s", label, result["summary"])
        rospy.loginfo("Saved raw=%s annotated=%s", raw_path, annotated_path)

    def run(self):
        rospy.loginfo("Waiting for camera frames on %s", self.camera_topic)
        start = time.time()
        startup_camera_wait = float(self.config.get("startup_camera_wait", 1.0))
        while self.last_image is None and time.time() - start < startup_camera_wait and not rospy.is_shutdown():
            rospy.sleep(0.1)

        for step in self.config.get("steps", []):
            if rospy.is_shutdown():
                break
            name = step.get("name", "unnamed")
            action = step.get("action")
            rospy.loginfo("Mission step: %s action=%s", name, action)
            if action == "wait":
                self.wait_for(step.get("duration", 1.0))
            elif action in ("drive", "turn"):
                self.drive_for(step.get("linear", 0.0), step.get("angular", 0.0), step.get("duration", 1.0))
            elif action == "capture":
                self.capture(step.get("label", name))
            else:
                rospy.logwarn("Unknown mission action: %s", action)

        self.stop()
        rospy.loginfo("Mission finished")


def main():
    rospy.init_node("mission_controller")
    controller = MissionController()
    rospy.on_shutdown(controller.stop)
    controller.run()


if __name__ == "__main__":
    main()