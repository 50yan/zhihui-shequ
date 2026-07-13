# ROS 复赛系统运行手册

## 1. ROS 虚拟机首次安装依赖

只需执行一次：

```bash
sudo apt update
sudo apt install -y \
  ros-noetic-gmapping \
  ros-noetic-navigation \
  ros-noetic-map-server \
  ros-noetic-amcl \
  ros-noetic-move-base \
  ros-noetic-gazebo-plugins \
  ros-noetic-robot-state-publisher \
  python3-yaml \
  python3-opencv
```

## 2. Windows 打包并提供下载

Windows PowerShell 终端 1：

```powershell
cd F:\桌面\147
tar -czf zhihui_shequ_ros.tgz zhihui_shequ_ros
python -m http.server 8000 --bind 0.0.0.0
```

这个终端需要保持打开。Windows 仓库是源文件，下面的同步会覆盖 ROS 虚拟机中的同名包；如果你刚在 ROS 虚拟机里修改了文件，必须先把修改取回 Windows，否则会丢失。

## 3. 同步到 ROS 虚拟机并编译

ROS 终端完整输入：

```bash
killall gzserver gzclient rosmaster roscore roslaunch 2>/dev/null
source /opt/ros/noetic/setup.bash
mkdir -p ~/incoming
cd ~/incoming
rm -f zhihui_shequ_ros.tgz
wget -O zhihui_shequ_ros.tgz http://10.0.2.2:8000/zhihui_shequ_ros.tgz
rm -rf zhihui_shequ_ros
tar -xzf zhihui_shequ_ros.tgz
rm -rf ~/zhihui_ws/src/zhihui_shequ_sim
cp -r ~/incoming/zhihui_shequ_ros/src/zhihui_shequ_sim ~/zhihui_ws/src/
cd ~/zhihui_ws
catkin_make
source devel/setup.bash
```

可选的项目测试：

```bash
cd ~/zhihui_ws
catkin_make run_tests
catkin_test_results
```

其中 `navigation_runtime.test` 会以无界面模式真实启动 Gazebo、雷达、相机、地图、AMCL 和 move_base，并检查 `/scan`、`/camera/image_raw`、`/odom`、`/map`、`/amcl_pose`、`map -> base_footprint` TF 和 move_base action server。

## 4. 检查雷达和相机

终端 1 启动基础仿真，不启动固定路线：

```bash
killall gzserver gzclient rosmaster roscore roslaunch 2>/dev/null
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
source devel/setup.bash
roslaunch zhihui_shequ_sim simulation.launch run_mission:=false show_camera_window:=false
```

终端 2 检查话题：

```bash
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
source devel/setup.bash
rostopic list | grep -E '^/scan$|^/camera/image_raw$|^/odom$|^/tf$'
rostopic hz /scan
rostopic echo -n 1 /scan | grep -E 'angle_min|angle_max|range_min|range_max'
```

`angle_min` 应接近 `-3.14159`，`angle_max` 应接近 `3.14159`。

## 5. 重新进行 Gmapping 建图

终端 1：

```bash
killall gzserver gzclient rosmaster roscore roslaunch 2>/dev/null
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
catkin_make
source devel/setup.bash
roslaunch zhihui_shequ_sim slam_mapping.launch
```

自动覆盖节点结束后，终端 2 保存地图：

```bash
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
source devel/setup.bash
rosrun map_server map_saver -f ~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10
ls -lh ~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10.*
```

建图时检查：

```bash
rostopic hz /map
rosrun tf tf_echo map base_footprint
```

## 6. 正式自主导航

每次打开正式比赛流程，完整输入：

```bash
killall gzserver gzclient rosmaster roscore roslaunch 2>/dev/null
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
catkin_make
source devel/setup.bash
roslaunch zhihui_shequ_sim competition_navigation.launch
```

只启动导航系统、暂不自动巡检：

```bash
roslaunch zhihui_shequ_sim competition_navigation.launch run_patrol:=false
```

另开终端检查定位和导航：

```bash
source /opt/ros/noetic/setup.bash
cd ~/zhihui_ws
source devel/setup.bash
rostopic echo -n 1 /amcl_pose
rostopic echo /zhihui_shequ/navigation_status
rostopic echo /move_base/status
```

## 7. 照片位置

每次正式巡检创建一个新目录：

```bash
ls -lah ~/camera
find ~/camera -maxdepth 2 -type f | sort
```

例如第一次运行保存到 `~/camera/1`，第二次运行保存到 `~/camera/2`。

## 8. 关键文件

- 正式场地：`~/zhihui_ws/src/zhihui_shequ_sim/worlds/smart_community_0_10.world`
- 机器人模型：`~/zhihui_ws/src/zhihui_shequ_sim/urdf/smart_car.xacro`
- SLAM 入口：`~/zhihui_ws/src/zhihui_shequ_sim/launch/slam_mapping.launch`
- 正式导航入口：`~/zhihui_ws/src/zhihui_shequ_sim/launch/competition_navigation.launch`
- 正式巡检点：`~/zhihui_ws/src/zhihui_shequ_sim/config/patrol_0_10.yaml`
- 上一版巡检点：`~/zhihui_ws/src/zhihui_shequ_sim/config/patrol.yaml`
- 0-10 场地建图覆盖点：`~/zhihui_ws/src/zhihui_shequ_sim/config/mapping_route_0_10.yaml`
- 上一版建图覆盖点：`~/zhihui_ws/src/zhihui_shequ_sim/config/mapping_route.yaml`
- 正式导航地图：`~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10.yaml`
- Gmapping 保存目标：`~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10.yaml`
