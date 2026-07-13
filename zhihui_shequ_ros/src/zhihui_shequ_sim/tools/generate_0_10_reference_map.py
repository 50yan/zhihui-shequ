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


def rectangle(draw, x_min, y_min, x_max, y_max, fill):
    left, bottom = world_to_pixel(x_min, y_min)
    right, top = world_to_pixel(x_max, y_max)
    draw.rectangle((left, top, right, bottom), fill=fill)


def build_map(output_path):
    image = Image.new("L", (WIDTH, HEIGHT), 205)
    draw = ImageDraw.Draw(image)

    # Match the selected world's outer walls and three inspection boards.
    rectangle(draw, -4.99, -4.99, 4.99, 4.99, fill=254)
    rectangle(draw, -5.20, 4.99, 5.20, 5.11, fill=0)
    rectangle(draw, -5.20, -5.11, 5.20, -4.99, fill=0)
    rectangle(draw, -5.11, -5.20, -4.99, 5.20, fill=0)
    rectangle(draw, 4.99, -5.20, 5.11, 5.20, fill=0)
    rectangle(draw, -2.45, 1.71, -0.45, 1.79, fill=0)
    rectangle(draw, -2.75, -1.39, -0.75, -1.31, fill=0)
    rectangle(draw, 4.01, -2.95, 4.09, -1.45, fill=0)
    image.save(output_path, format="PPM")


if __name__ == "__main__":
    default_output = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "maps",
        "smart_community_0_10.pgm",
    )
    parser = argparse.ArgumentParser(description="Generate the smart community 0-10 occupancy map")
    parser.add_argument("output", nargs="?", default=default_output)
    args = parser.parse_args()
    build_map(args.output)
