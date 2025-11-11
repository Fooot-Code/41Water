# settings.py
import pygame

TITLE = "41 Water"
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# Pixel scaling: draw on small surfaces then scale up for chunky look
PIXEL_SCALE = 3  # scale factor for final blit
VIRTUAL_WIDTH = SCREEN_WIDTH // PIXEL_SCALE
VIRTUAL_HEIGHT = SCREEN_HEIGHT // PIXEL_SCALE

GRAVITY = 0.6
TERMINAL_VEL = 12

# Player tunables
PLAYER_SPEED = 2.2
PLAYER_JUMP_SPEED = -9.0
PLAYER_WIDTH = 12
PLAYER_HEIGHT = 18

# Level settings
LEVEL_WIDTH = VIRTUAL_WIDTH * 3  # Level is 3 screens wide
LEVEL_HEIGHT = VIRTUAL_HEIGHT

# Colors (in 0-255 tuples)
WHITE = (255,255,255)
BLACK = (0,0,0)
UI_BG = (20, 20, 30)

# Combat settings (Hollow Knight-inspired)
KNOCKBACK_FORCE = 4
HITSTOP_DURATION = 0.1
INVINCIBILITY_DURATION = 0.6
