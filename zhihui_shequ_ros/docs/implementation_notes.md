# 智慧社区实现说明

## 对应赛题要求

省赛综合测试要求包括：

1. 使用 ROS1 和 Gazebo 创建仿真环境。
2. 在场地中加入人群立牌和车牌立牌。
3. 建立带运动控制和摄像头的车辆模型。
4. 按路线自主运动，并在识别点停车采集图片。
5. 对人员区域和车辆识别区图片进行识别并展示结果。
6. 录屏展示模型、建图/运动、识别过程和代码讲解。

当前工程对应实现：

- `worlds/smart_community.world`：简化智慧社区场地、人群立牌、车牌立牌、红绿灯、停车位。
- `urdf/smart_car.xacro`：差速小车、前置摄像头、Gazebo 差速驱动插件。
- `scripts/mission_controller.py`：路线执行、停车、图像采集、识别结果输出。
- `scripts/vision_tools.py`：OpenCV 颜色区域检测，提供人员/外来人员/车牌候选框标注。
- `config/mission.yaml`：任务路线和采集点配置。

## 技术路线

车辆控制采用 ROS `geometry_msgs/Twist`，由 Gazebo `libgazebo_ros_diff_drive.so` 插件执行差速运动。

图像采集使用 Gazebo 相机插件发布 `/camera/image_raw`，Python 节点通过 `cv_bridge` 转换为 OpenCV 图像。

识别逻辑当前使用颜色分割和轮廓提取：

- 蓝色圆柱代表社区人员。
- 红色圆柱代表外来人员。
- 蓝色横向矩形代表车牌候选。

该方式适合演示完整链路。拿到官方素材后，可以在 `vision_tools.py` 中替换为 YOLO、模板匹配、OCR 或其他模型推理逻辑，外部接口不需要改动。

## 编译运行

```bash
source /opt/ros/noetic/setup.bash
mkdir -p ~/catkin_ws/src
cp -r /media/sf_sim_files/zhihui_shequ_ros/src/zhihui_shequ_sim ~/catkin_ws/src/
cd ~/catkin_ws
catkin_make
source devel/setup.bash
roslaunch zhihui_shequ_sim simulation.launch
```

## 输出

图片保存到：

```bash
~/.ros/zhihui_shequ/captures
```

每个采集点会生成：

- 原始图片：`*_raw.jpg`
- 标注图片：`*_annotated.jpg`

终端会输出识别摘要。

## 后续增强

1. 替换官方地图贴图和立牌模型。
2. 根据官方地图重新标定 `mission.yaml` 中的路线时长。
3. 接入真实识别模型，例如 YOLO 目标检测和 EasyOCR/CRNN 车牌识别。
4. 增加 SLAM 或建图流程录屏，例如 `gmapping`/`cartographer`，用于满足“建图过程”展示。

## 当前验证记录

在 VirtualBox 虚拟机 `ROS2` 中验证，实际环境为 Ubuntu 20.04 + ROS Noetic。

已通过：

- `catkin_make` 编译通过。
- `rospack find zhihui_shequ_sim` 可找到包。
- `xacro` 可展开车辆模型。
- `roslaunch zhihui_shequ_sim simulation.launch gui:=false run_mission:=false` 可启动 Gazebo 并生成车辆。
- `roslaunch zhihui_shequ_sim simulation.launch gui:=false run_mission:=true` 可完成路线步骤、三次采集和识别输出。

本机验证时 Gazebo 相机话题未发布，任务节点会记录 warning 并使用合成测试图兜底，已生成如下识别结果：

- `people_a`: residents=2 outsiders=1
- `people_b`: residents=2 outsiders=0
- `plate`: plate_candidates=2

输出图片位于虚拟机：

```bash
/home/rosuser/.ros/zhihui_shequ/captures
```

拿到官方模型或修复本机 Gazebo 相机插件后，任务节点会自动优先使用 `/camera/image_raw` 的真实图像。