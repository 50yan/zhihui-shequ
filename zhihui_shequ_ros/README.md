# 智慧社区 ROS1 复赛系统

本项目使用 ROS1 Noetic、Gazebo Classic、Gmapping、AMCL 和 move_base，完成智慧社区仿真场地中的建图、定位、导航、避障和巡检拍照。

正式导航和 SLAM 当前默认使用 `worlds/smart_community_0_10.world`；上一版重建场地仍保留在 `worlds/smart_community.world`。
正式巡检路线使用 `config/patrol_0_10.yaml`，与该场地的两个人偶板和一个车牌板位置对应。

当前正式能力：

- 1 个 360 度激光雷达，发布 `/scan`
- 1 个单目相机，发布 `/camera/image_raw`
- Gmapping 自主建图与自动覆盖路线
- map_server + AMCL 自主定位
- move_base 多点自主导航与雷达避障
- 到达巡检点后拍照，每次运行保存到独立的 `~/camera/N` 文件夹
- 独立相机窗口显示 AMCL 位姿、当前目标、move_base 状态和最新照片

红绿灯、人偶、车牌和楼房火灾的正式视觉算法暂未实现；当前场地仅保留简单几何占位和原有基础 OpenCV 代码，等待正式图片或模型后再替换。

## 正式入口

```bash
roslaunch zhihui_shequ_sim competition_navigation.launch
```

正式入口使用 AMCL 和 move_base，不会启动旧的 `mission_controller.py` 固定时间路线。

需要临时恢复上一版重建场地时，world 和 map 必须同时指定：

```bash
roslaunch zhihui_shequ_sim competition_navigation.launch \
  world:=$(rospack find zhihui_shequ_sim)/worlds/smart_community.world \
  map_file:=$(rospack find zhihui_shequ_sim)/maps/smart_community_slam.yaml
```

## SLAM 建图入口

```bash
roslaunch zhihui_shequ_sim slam_mapping.launch
```

自动覆盖结束后保存地图：

```bash
rosrun map_server map_saver -f ~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10
```

## 旧固定路线

```bash
roslaunch zhihui_shequ_sim simulation.launch
```

旧场地备份在 `src/zhihui_shequ_sim/worlds/legacy/smart_community_fixed_route.world`，旧固定路线只用于回看，不作为复赛正式流程。

完整同步、安装和检查命令见 [docs/SLAM_NAVIGATION_GUIDE.md](docs/SLAM_NAVIGATION_GUIDE.md)。
