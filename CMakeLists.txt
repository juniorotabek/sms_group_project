cmake_minimum_required(VERSION 3.0.2)
project(smart_warehouse_robot)

find_package(catkin REQUIRED COMPONENTS
  geometry_msgs
  rospy
  std_msgs
  std_srvs
  tf
  visualization_msgs
)

catkin_python_setup()

catkin_package()

catkin_install_python(PROGRAMS
  scripts/task_publisher_node.py
  scripts/task_queue_manager_node.py
  scripts/waypoint_goal_publisher_node.py
  scripts/path_progress_monitor_node.py
  scripts/obstacle_detector_node.py
  scripts/emergency_stop_node.py
  scripts/battery_publisher_node.py
  scripts/charging_controller_node.py
  scripts/package_handler_node.py
  scripts/status_publisher_node.py
  scripts/diagnostic_logger_node.py
  scripts/rviz_delivery_visualizer_node.py
  scripts/smart_warehouse_cli.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(PROGRAMS
  scripts/record_demo_bag.sh
  scripts/replay_demo_bag.sh
  scripts/check_demo_bag.sh
  scripts/run_demo_instructions.sh
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config docs bags
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
