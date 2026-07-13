cmake_minimum_required(VERSION 3.0.2)
project(zhihui_shequ_sim)

find_package(catkin REQUIRED COMPONENTS
  actionlib
  actionlib_msgs
  cv_bridge
  gazebo_ros
  gazebo_plugins
  rosgraph_msgs
  geometry_msgs
  gmapping
  nav_msgs
  move_base_msgs
  rospy
  robot_state_publisher
  sensor_msgs
  std_msgs
  std_srvs
  xacro
)

catkin_package()

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  catkin_add_nosetests(tests)
  add_rostest(tests/navigation_runtime.test)
endif()

catkin_install_python(PROGRAMS
  scripts/mission_controller.py
  scripts/mapping_explorer.py
  scripts/patrol_navigation.py
  scripts/navigation_runtime_test.py
  scripts/delete_existing_model.py
  scripts/reset_spawn_model.py
  scripts/vision_node.py
  scripts/navigation_status_window.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(FILES
  scripts/navigation_core.py
  scripts/vision_tools.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  config
  launch
  maps
  media
  urdf
  worlds
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
