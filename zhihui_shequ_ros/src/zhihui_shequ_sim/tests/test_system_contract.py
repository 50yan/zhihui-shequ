#!/usr/bin/env python3
import math
import os
import unittest
import xml.etree.ElementTree as ET

import yaml


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def package_path(*parts):
    return os.path.join(PACKAGE_DIR, *parts)


class SystemContractTest(unittest.TestCase):
    def test_robot_has_one_360_lidar_and_one_monocular_camera(self):
        root = ET.parse(package_path("urdf", "smart_car.xacro")).getroot()
        sensors = root.findall(".//sensor")
        ray_sensors = [sensor for sensor in sensors if sensor.get("type") in ("ray", "gpu_ray")]
        cameras = [sensor for sensor in sensors if sensor.get("type") == "camera"]

        self.assertEqual(1, len(ray_sensors))
        self.assertEqual(1, len(cameras))

        horizontal = ray_sensors[0].find("./ray/scan/horizontal")
        self.assertIsNotNone(horizontal)
        minimum = float(horizontal.findtext("min_angle"))
        maximum = float(horizontal.findtext("max_angle"))
        self.assertAlmostEqual(2.0 * math.pi, maximum - minimum, places=3)

        lidar_plugin = ray_sensors[0].find("plugin")
        self.assertIsNotNone(lidar_plugin)
        self.assertEqual("/scan", lidar_plugin.findtext("topicName"))
        self.assertEqual("lidar_link", lidar_plugin.findtext("frameName"))

    def test_formal_navigation_launch_wires_the_navigation_stack(self):
        root = ET.parse(package_path("launch", "competition_navigation.launch")).getroot()
        packages = {node.get("pkg") for node in root.findall(".//node")}
        node_types = {node.get("type") for node in root.findall(".//node")}

        self.assertIn("map_server", packages)
        self.assertIn("amcl", packages)
        self.assertIn("move_base", packages)
        self.assertIn("patrol_navigation.py", node_types)
        self.assertIn("navigation_status_window.py", node_types)
        self.assertNotIn("mission_controller.py", node_types)

        args = {arg.get("name"): arg.get("default") for arg in root.findall("arg")}
        self.assertIn("worlds/smart_community_0_10.world", args["world"])
        self.assertIn("maps/smart_community_0_10.yaml", args["map_file"])
        self.assertIn("config/patrol_0_10.yaml", args["patrol_config"])

    def test_slam_launch_wires_gmapping_and_real_motion_explorer(self):
        root = ET.parse(package_path("launch", "slam_mapping.launch")).getroot()
        packages = {node.get("pkg") for node in root.findall(".//node")}
        node_types = {node.get("type") for node in root.findall(".//node")}

        self.assertIn("gmapping", packages)
        self.assertIn("mapping_explorer.py", node_types)
        args = {arg.get("name"): arg.get("default") for arg in root.findall("arg")}
        self.assertIn("worlds/smart_community_0_10.world", args["world"])
        self.assertIn("config/mapping_route_0_10.yaml", args["explorer_config"])

    def test_legacy_launch_keeps_the_fixed_route_with_its_original_world(self):
        root = ET.parse(package_path("launch", "simulation.launch")).getroot()
        world_arg = next(arg for arg in root.findall("arg") if arg.get("name") == "world")
        self.assertIn("worlds/legacy/smart_community_fixed_route.world", world_arg.get("default"))

    def test_world_contains_competition_areas_and_lidar_visible_obstacles(self):
        root = ET.parse(package_path("worlds", "smart_community.world")).getroot()
        models = {model.get("name"): model for model in root.findall(".//model")}
        required = {
            "people_area_a",
            "people_area_b",
            "building_a",
            "building_b",
            "building_c",
            "building_d",
            "station_room",
            "traffic_light_north",
            "traffic_light_south",
            "parking_zone",
        }
        self.assertTrue(required.issubset(models), required - set(models))

        for name in required - {"parking_zone"}:
            self.assertTrue(models[name].findall(".//collision"), name)

    def test_selected_0_10_world_has_lidar_visible_inspection_boards(self):
        root = ET.parse(package_path("worlds", "smart_community_0_10.world")).getroot()
        models = {model.get("name"): model for model in root.findall(".//model")}
        for name in ("people_area_1_board", "people_area_2_board", "plate_board"):
            self.assertTrue(models[name].findall(".//collision"), name)

        with open(package_path("config", "patrol_0_10.yaml"), "r", encoding="utf-8") as stream:
            patrol = yaml.safe_load(stream)
        captures = {waypoint.get("capture") for waypoint in patrol["waypoints"] if waypoint.get("capture")}
        self.assertEqual({"people_a", "people_b", "plate"}, captures)

    def test_official_marked_gaps_are_exactly_060_metres(self):
        root = ET.parse(package_path("worlds", "smart_community.world")).getroot()

        def collision(name):
            item = root.find(".//collision[@name='%s']" % name)
            pose = [float(value) for value in item.findtext("pose").split()]
            size = [float(value) for value in item.findtext("geometry/box/size").split()]
            return pose, size

        people_top, _ = collision("people_a_top_boundary")
        people_bottom, _ = collision("people_a_bottom_boundary")
        people_height = people_top[1] - people_bottom[1]

        left_bottom, _ = collision("left_block_bottom_boundary")
        south_wall, south_size = collision("south_collision")
        south_inner_face = south_wall[1] + south_size[1] / 2.0
        bottom_gap = left_bottom[1] - south_inner_face

        building_c = root.find(".//model[@name='building_c']")
        building_x = float(building_c.findtext("pose").split()[0])
        building_width = float(building_c.findtext(".//collision/geometry/box/size").split()[0])
        building_east = building_x + building_width / 2.0
        parking_wall, _ = collision("parking_boundary")
        right_gap = parking_wall[0] - building_east

        self.assertAlmostEqual(0.60, people_height, places=3)
        self.assertAlmostEqual(0.60, bottom_gap, places=3)
        self.assertAlmostEqual(0.60, right_gap, places=3)

    def test_navigation_configuration_and_map_are_loadable(self):
        config_names = (
            "costmap_common.yaml",
            "global_costmap.yaml",
            "local_costmap.yaml",
            "base_local_planner.yaml",
            "move_base.yaml",
            "amcl.yaml",
            "mapping_route.yaml",
            "mapping_route_0_10.yaml",
            "patrol.yaml",
            "patrol_0_10.yaml",
        )
        for name in config_names:
            with open(package_path("config", name), "r", encoding="utf-8") as stream:
                data = yaml.safe_load(stream)
            self.assertIsInstance(data, dict, name)

        with open(package_path("config", "costmap_common.yaml"), "r", encoding="utf-8") as stream:
            costmap = yaml.safe_load(stream)
        self.assertGreaterEqual(costmap["inflation_layer"]["inflation_radius"], 0.27)

        map_files = {
            "smart_community_slam.yaml": "smart_community_slam.pgm",
            "smart_community_0_10.yaml": "smart_community_0_10.pgm",
        }
        for yaml_name, expected_image in map_files.items():
            with open(package_path("maps", yaml_name), "r", encoding="utf-8") as stream:
                map_config = yaml.safe_load(stream)
            self.assertEqual(expected_image, map_config["image"])
            self.assertGreater(map_config["resolution"], 0.0)
            image_path = package_path("maps", map_config["image"])
            self.assertTrue(os.path.isfile(image_path))
            with open(image_path, "rb") as stream:
                tokens = []
                while len(tokens) < 4:
                    line = stream.readline()
                    self.assertTrue(line, "incomplete PGM header")
                    if line.startswith(b"#"):
                        continue
                    tokens.extend(line.split())
                self.assertEqual(b"P5", tokens[0])
                self.assertGreater(int(tokens[1]), 0)
                self.assertGreater(int(tokens[2]), 0)
                self.assertEqual(255, int(tokens[3]))

    def test_patrol_has_unique_multi_point_goals_and_capture_stops(self):
        with open(package_path("config", "patrol.yaml"), "r", encoding="utf-8") as stream:
            patrol = yaml.safe_load(stream)
        waypoints = patrol["waypoints"]
        names = [waypoint["name"] for waypoint in waypoints]
        captures = {waypoint.get("capture") for waypoint in waypoints if waypoint.get("capture")}

        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(waypoints), 8)
        self.assertTrue({"people_a", "people_b", "plate"}.issubset(captures))


if __name__ == "__main__":
    unittest.main()
