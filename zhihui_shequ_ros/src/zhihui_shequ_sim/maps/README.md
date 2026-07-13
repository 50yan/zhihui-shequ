# Smart community maps

`smart_community_0_10.yaml` and `smart_community_0_10.pgm` are the formal
navigation map pair for `worlds/smart_community_0_10.world`. The checked-in map
matches that world's physical collision geometry: a free interior bounded by
four outer walls.

After running `slam_mapping.launch`, replace the formal map with:

```bash
rosrun map_server map_saver -f ~/zhihui_ws/src/zhihui_shequ_sim/maps/smart_community_0_10
```

`smart_community_slam.*` remains in the repository as the previous rebuilt
competition-field map. Restore it only together with
`worlds/smart_community.world`:

```bash
roslaunch zhihui_shequ_sim competition_navigation.launch \
  world:=$(rospack find zhihui_shequ_sim)/worlds/smart_community.world \
  map_file:=$(rospack find zhihui_shequ_sim)/maps/smart_community_slam.yaml
```
