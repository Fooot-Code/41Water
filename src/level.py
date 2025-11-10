# level.py
import pygame
from assets import generate_tile
from settings import VIRTUAL_WIDTH, VIRTUAL_HEIGHT
from pygame import Rect

TILE_SIZE = 16 * 3  # because tiles are generated and scaled by PIXEL_SCALE=3 by default

def build_level_from_array(arr):
    """Create tiles and rects from a 2D array of characters."""
    tiles = []
    tile_surfaces = []
    rows = len(arr)
    cols = max(len(r) for r in arr)
    for y, row in enumerate(arr):
        for x, ch in enumerate(row):
            if ch == "G":
                surf = generate_tile("grass")
                rect = surf.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))
                tiles.append(rect)
                tile_surfaces.append((surf, rect.topleft))
            elif ch == "R":
                surf = generate_tile("rock")
                rect = surf.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))
                tiles.append(rect)
                tile_surfaces.append((surf, rect.topleft))
    return tiles, tile_surfaces

# Sample levels: each is a small array of strings
LEVELS = []

LEVELS.append([  # level 1 - grass plains
    "........................................................................................",
    "........................................................................................",
    "...P....................................................................................",
    "........................................................................................",
    ".............GGG......................GGGG.....................GGG........................",
    "...........GGGGGGG...........GGGGGGGGGGGGG.................GGGGGGG......................",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
])

LEVELS.append([  # level 2 - rocky caverns
    "........................................................................................",
    "......................R..............................R....................................",
    "...........RRRRRRRRRRRRR..............R.................RRRRR...........................",
    "..................R...R.................................R.................................",
    ".......P................................................................................",
    "........................................................................................",
    "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
])

LEVELS.append([  # level 3 - temple near 41 Water
    "........................................................................................",
    "........................................................................................",
    "............GGGGGGG.......GGG....................P.............GGGGGGG..................",
    "........................................................................................",
    ".............GGGGGGGGG........GGGGGGG..........GGG.........GGGGGGGGG...................",
    "........................................................................................",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
])
