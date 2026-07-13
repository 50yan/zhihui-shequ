# Smart community map

`smart_community_slam.pgm` is a checked-in reference map generated from the same
static collision geometry as `worlds/smart_community.world`. It lets the formal
navigation launch start before a fresh mapping run.

For the competition demonstration, run `slam_mapping.launch`, let the explorer
finish, then overwrite this map with:

```bash
rosrun map_server map_saver -f ~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_slam
```
