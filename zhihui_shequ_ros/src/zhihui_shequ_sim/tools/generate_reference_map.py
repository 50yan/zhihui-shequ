#!/usr/bin/env python3
import argparse
import os

from PIL import Image, ImageDraw


RESOLUTION = 0.05
ORIGIN_X = -6.0
ORIGIN_Y = -6.0
WIDTH = 240
HEIGHT = 240


def world_to_pixel(x, y):
    px = int(round((x - ORIGIN_X) / RESOLUTION))
    py = HEIGHT - 1 - int(round((y - ORIGIN_Y) / RESOLUTION))
    return px, py


def rectangle(draw, x_min, y_min, x_max, y_max, fill=0):
    left, bottom = world_to_pixel(x_min, y_min)
    right, top = world_to_pixel(x_max, y_max)
    draw.rectangle((left, top, right, bottom), fill=fill)


def build_map(output_path):
    image = Image.new("L", (WIDTH, HEIGHT), 205)
    draw = ImageDraw.Draw(image)
    rectangle(draw, -4.75, -4.75, 4.75, 4.75, fill=254)

    # Outer walls.
    rectangle(draw, -4.85, 4.75, 4.85, 4.85)
    rectangle(draw, -4.85, -4.85, 4.85, -4.75)
    rectangle(draw, -4.85, -4.85, -4.75, 4.85)
    rectangle(draw, 4.75, -4.85, 4.85, 4.85)

    # Inspection boards and buildings.
    rectangle(draw, -3.50, 3.21, -0.80, 3.29)
    rectangle(draw, -3.58, 0.82, -1.32, 0.90)
    rectangle(draw, 0.60, 1.92, 2.40, 2.98)
    rectangle(draw, 0.60, 0.37, 2.40, 1.43)
    rectangle(draw, 0.60, -1.18, 2.40, -0.12)
    rectangle(draw, -3.63, -3.58, -2.87, -1.32)
    rectangle(draw, -2.68, -3.33, -1.22, -1.97)
    rectangle(draw, 2.14, -3.23, 2.22, -1.67)

    # Lidar-visible boundaries for the three official 0.60 m markings.
    rectangle(draw, -3.80, 3.52, -0.50, 3.58)
    rectangle(draw, -3.80, 2.92, -0.50, 2.98)
    rectangle(draw, -3.83, 2.95, -3.77, 3.55)
    rectangle(draw, 2.97, -3.20, 3.03, 3.20)
    rectangle(draw, -3.80, -4.18, -1.10, -4.12)

    # Traffic lights and parked cars.
    rectangle(draw, -1.33, 4.11, -0.97, 4.29)
    rectangle(draw, -0.09, -4.13, 0.09, -3.77)
    rectangle(draw, 3.32, -1.98, 4.48, -1.42)
    rectangle(draw, 3.32, -0.28, 4.48, 0.28)
    rectangle(draw, 3.32, 1.42, 4.48, 1.98)

    image.save(output_path, format="PPM")


if __name__ == "__main__":
    default_output = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "maps",
        "smart_community_slam.pgm",
    )
    parser = argparse.ArgumentParser(description="Generate the reference occupancy map from field geometry")
    parser.add_argument("output", nargs="?", default=default_output)
    args = parser.parse_args()
    build_map(args.output)
