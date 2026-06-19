# 智慧社区 ROS1 仿真工程

本工程面向 2025 AIC 算法应用赛“智慧社区”省赛综合测试，提供一个 ROS1 Noetic + Gazebo 的基础实现：

- Gazebo 智慧社区仿真场地
- 差速小车模型，包含摄像头
- 自动路线控制和定点停车
- 人群区域、车牌区域的图像采集
- 基础 OpenCV 视觉识别与标注框架
- 可替换官方素材的模型、配置和运行入口

## 环境

已验证目标虚拟机：

- Ubuntu 20.04
- ROS Noetic
- Gazebo classic

每次打开新终端先执行：

```bash
source /opt/ros/noetic/setup.bash
```

## 编译

```bash
cd ~/catkin_ws
mkdir -p src
cp -r /media/sf_sim_files/zhihui_shequ_ros/src/zhihui_shequ_sim src/
catkin_make
source devel/setup.bash
```

如果 VirtualBox 共享目录挂载位置不是 `/media/sf_sim_files`，请把上面的路径替换成实际路径。

## 启动仿真

```bash
roslaunch zhihui_shequ_sim simulation.launch
```

默认会启动 Gazebo、生成车辆，并启动任务控制节点。车辆会按配置路线移动，在人员区域和车牌区域停车拍照。

只启动场景和车辆，不自动跑任务：

```bash
roslaunch zhihui_shequ_sim simulation.launch run_mission:=false
```

## 运行结果

图片和识别标注默认保存到：

```bash
~/.ros/zhihui_shequ/captures
```

任务节点会在终端输出识别摘要，例如：

- 人员区域检测到若干人形目标
- 车牌区域检测到候选车牌区域
- 标注图片保存路径

## 目录结构

```text
zhihui_shequ_ros/
  src/
    zhihui_shequ_sim/
      config/
      launch/
      scripts/
      urdf/
      worlds/
      CMakeLists.txt
      package.xml
```

## 后续替换官方素材

赛题 PDF 中给出的百度网盘素材包含官方地图和模型。拿到素材后建议替换：

1. `worlds/smart_community.world` 中的简化场地
2. `config/mission.yaml` 中的路线和停车点时间
3. `scripts/vision_tools.py` 中的识别逻辑或模型推理入口

当前版本的重点是完整跑通 ROS/Gazebo/路线/拍照/识别/保存链路，便于后续把官方模型和更强识别算法接入。
