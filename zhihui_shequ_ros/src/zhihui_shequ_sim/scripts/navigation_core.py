#!/usr/bin/env python3
import math
import os


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def normalize_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def waypoint_command(
    current_x,
    current_y,
    current_yaw,
    target_x,
    target_y,
    max_linear,
    max_angular,
    distance_tolerance,
):
    dx = float(target_x) - float(current_x)
    dy = float(target_y) - float(current_y)
    distance = math.hypot(dx, dy)
    if distance <= float(distance_tolerance):
        return 0.0, 0.0, True

    target_heading = math.atan2(dy, dx)
    heading_error = normalize_angle(target_heading - float(current_yaw))
    angular = clamp(1.8 * heading_error, -float(max_angular), float(max_angular))

    if abs(heading_error) > 0.35:
        return 0.0, angular, False

    heading_scale = max(0.25, 1.0 - abs(heading_error) / 0.35)
    linear = min(float(max_linear), max(0.12, 0.8 * distance)) * heading_scale
    return linear, angular, False


def choose_avoidance_turn(left_clearance, right_clearance, speed):
    return abs(float(speed)) if float(left_clearance) >= float(right_clearance) else -abs(float(speed))


def data_is_fresh(last_time, now, timeout):
    return last_time is not None and float(now) - float(last_time) <= float(timeout)


def patrol_result(total, succeeded, failed, captures, expected_captures):
    if (
        int(failed)
        or int(succeeded) != int(total)
        or int(captures) != int(expected_captures)
    ):
        return (
            "incomplete",
            "patrol incomplete: goals=%d/%d failed=%d captures=%d/%d"
            % (succeeded, total, failed, captures, expected_captures),
        )
    return "finished", "patrol finished: goals=%d captures=%d/%d" % (
        succeeded,
        captures,
        expected_captures,
    )


def next_numbered_directory(output_root):
    root = os.path.expandvars(os.path.expanduser(output_root))
    os.makedirs(root, exist_ok=True)
    run_ids = []
    for name in os.listdir(root):
        path = os.path.join(root, name)
        if os.path.isdir(path) and name.isdigit():
            run_ids.append(int(name))
    return os.path.join(root, str(max(run_ids, default=0) + 1))
