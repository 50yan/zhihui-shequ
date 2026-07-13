cmake_minimum_required(VERSION 3.0.2)
project(zhihui_shequ_sim)

find_package(catkin REQUIRED COMPONENTS
  cv_bridge
  gazebo_ros
  rosgraph_msgs
  geometry_msgs
  nav_msgs
  rospy
  sensor_msgs
  std_msgs
  std_srvs
  xacro
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/mission_controller.py
  scripts/delete_existing_model.py
  scripts/reset_spawn_model.py
  scripts/vision_node.py
  scripts/navigation_status_window.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  config
  launch
  media
  urdf
  worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
