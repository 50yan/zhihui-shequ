#!/usr/bin/env python3
import math
import os
import sys
import time

import rospy
import yaml
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

script_dir = os.path.dirname(os.path.abspath(globals().get("__file__", globals().get("python_script", sys.argv[0]))))
sys.path.insert(0, script_dir)
from navigation_core import choose_avoidance_turn, data_is_fresh, waypoint_command


def yaw_from_quaternion(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


class MappingExplorer:
    def __init__(self):
        config_path = rospy.get_param("~config")
        with open(config_path, "r", encoding="utf-8") as stream:
            self.config = yaml.safe_load(stream)

        self.pose = None
        self.front_clearance = float("inf")
        self.left_clearance = float("inf")
        self.right_clearance = float("inf")
        self.last_scan_wall_time = None

        self.max_linear = float(self.config.get("max_linear", 0.45))
        self.max_angular = float(self.config.get("max_angular", 0.9))
        self.distance_tolerance = float(self.config.get("distance_tolerance", 0.18))
        self.obstacle_stop_distance = float(self.config.get("obstacle_stop_distance", 0.42))
        self.scan_timeout = float(self.config.get("scan_timeout", 1.0))
        self.avoidance_angular = float(self.config.get("avoidance_angular", 0.75))
        self.avoid_turn_duration = float(self.config.get("avoid_turn_duration", 1.0))
        self.avoid_forward_duration = float(self.config.get("avoid_forward_duration", 1.2))
        self.avoid_forward_speed = float(self.config.get("avoid_forward_speed", 0.18))
        self.waypoint_timeout = float(self.config.get("waypoint_timeout", 90.0))
        self.avoid_phase = None
        self.avoid_deadline = 0.0
        self.avoid_direction = 1.0

        cmd_topic = self.config.get("cmd_vel_topic", "/cmd_vel")
        odom_topic = self.config.get("odom_topic", "/odom")
        scan_topic = self.config.get("scan_topic", "/scan")
        self.cmd_pub = rospy.Publisher(cmd_topic, Twist, queue_size=10)
        rospy.Subscriber(odom_topic, Odometry, self._on_odom, queue_size=1)
        rospy.Subscriber(scan_topic, LaserScan, self._on_scan, queue_size=1)
        rospy.loginfo("Mapping explorer uses odom=%s scan=%s cmd_vel=%s", odom_topic, scan_topic, cmd_topic)

    def _on_odom(self, msg):
        pose = msg.pose.pose
        self.pose = (pose.position.x, pose.position.y, yaw_from_quaternion(pose.orientation))

    def _on_scan(self, msg):
        sectors = {"front": [], "left": [], "right": []}
        angle = msg.angle_min
        for distance in msg.ranges:
            if math.isfinite(distance) and msg.range_min <= distance <= msg.range_max:
                degrees = math.degrees(angle)
                if -25.0 <= degrees <= 25.0:
                    sectors["front"].append(distance)
                elif 25.0 < degrees <= 105.0:
                    sectors["left"].append(distance)
                elif -105.0 <= degrees < -25.0:
                    sectors["right"].append(distance)
            angle += msg.angle_increment

        self.front_clearance = min(sectors["front"], default=float("inf"))
        self.left_clearance = min(sectors["left"], default=float("inf"))
        self.right_clearance = min(sectors["right"], default=float("inf"))
        self.last_scan_wall_time = time.time()

    def _publish(self, linear=0.0, angular=0.0):
        twist = Twist()
        twist.linear.x = float(linear)
        twist.angular.z = float(angular)
        self.cmd_pub.publish(twist)

    def stop(self):
        self._publish()

    def _sensors_ready(self):
        return self.pose is not None and self.last_scan_wall_time is not None

    def _scan_is_fresh(self, now):
        return data_is_fresh(self.last_scan_wall_time, now, self.scan_timeout)

    def _start_avoidance(self, now):
        self.avoid_direction = 1.0 if choose_avoidance_turn(
            self.left_clearance,
            self.right_clearance,
            1.0,
        ) > 0.0 else -1.0
        self.avoid_phase = "turn"
        self.avoid_deadline = now + self.avoid_turn_duration

    def _run_avoidance(self, now):
        if self.avoid_phase == "turn":
            if now < self.avoid_deadline:
                self._publish(0.0, self.avoid_direction * self.avoidance_angular)
                return True
            self.avoid_phase = "forward"
            self.avoid_deadline = now + self.avoid_forward_duration

        if self.avoid_phase == "forward":
            if self.front_clearance < self.obstacle_stop_distance:
                self._start_avoidance(now)
                self._publish(0.0, self.avoid_direction * self.avoidance_angular)
                return True
            if now < self.avoid_deadline:
                self._publish(self.avoid_forward_speed, 0.0)
                return True
            self.avoid_phase = None
        return False

    def run(self):
        rospy.loginfo("Waiting for /odom and /scan before automatic SLAM exploration")
        wait_start = time.time()
        while not rospy.is_shutdown() and not self._sensors_ready():
            if time.time() - wait_start > 30.0:
                raise RuntimeError("Mapping explorer did not receive /odom and /scan within 30 seconds")
            rospy.sleep(0.1)

        rate = rospy.Rate(15.0)
        for waypoint in self.config.get("waypoints", []):
            name = waypoint.get("name", "unnamed")
            target_x = float(waypoint["x"])
            target_y = float(waypoint["y"])
            deadline = time.time() + self.waypoint_timeout
            rospy.loginfo("SLAM exploration target: %s x=%.2f y=%.2f", name, target_x, target_y)

            while not rospy.is_shutdown() and time.time() < deadline:
                now = time.time()
                if not self._scan_is_fresh(now):
                    self.stop()
                    rospy.logwarn_throttle(2.0, "Mapping explorer stopped: /scan data is stale")
                    rate.sleep()
                    continue
                if self._run_avoidance(now):
                    rate.sleep()
                    continue

                current_x, current_y, current_yaw = self.pose
                linear, angular, reached = waypoint_command(
                    current_x,
                    current_y,
                    current_yaw,
                    target_x,
                    target_y,
                    self.max_linear,
                    self.max_angular,
                    self.distance_tolerance,
                )
                if reached:
                    self.stop()
                    rospy.loginfo("Reached SLAM exploration target: %s", name)
                    break

                if linear > 0.0 and self.front_clearance < self.obstacle_stop_distance:
                    self._start_avoidance(now)
                    self._publish(0.0, self.avoid_direction * self.avoidance_angular)
                    rate.sleep()
                    continue
                self._publish(linear, angular)
                rate.sleep()
            else:
                rospy.logwarn("SLAM exploration target timed out: %s", name)
                self.stop()

        self.stop()
        rospy.loginfo("Automatic SLAM exploration finished; save the map with map_saver")


def main():
    rospy.init_node("mapping_explorer")
    explorer = MappingExplorer()
    rospy.on_shutdown(explorer.stop)
    explorer.run()


if __name__ == "__main__":
    main()
