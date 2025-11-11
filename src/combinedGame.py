#!/usr/bin/env python3
"""
41 Water - Extended: RPG / Turn-based overlay + Inventory + Branching Endings

This is an edited/extended single-file game based on the uploaded
combinedGame.py. It adds:
- Character stats (Strength, Agility, Magic)
- Inventory system (press I)
- Turn-based tactical combat (press T near enemies)
- Branching guide choice in final stage (B = befriend, F = fight)
- Multiple endings affected by player choices
- README writing option: run with --write-readme to create README.md

Dependencies:
- pygame (pip install pygame)

Controls:
- Arrow keys / A/D: move
- W / UP / Space: jump
- J: attack (action combat)
- K: dash
- T: attempt to enter turn-based combat if near enemies
- I: inventory (navigate with left/right, use with U, discard with D, exit with Esc)
- B/F during guide prompt to befriend/fight
- Enter to proceed on some screens
- Esc to quit
"""

# --- README content (will be written if run with --write-readme) ---
README_TEXT = """
41 Water - Extended (single-file)

Features:
- Choose a class: Wizard, Worrier, Warrior. Each has Strength, Agility, Magic stats.
- Action-platformer core with dash/jump/attack.
- Tactical turn-based combat overlay (press T near enemies).
- Inventory system (press I) — use potions, equip temporary buffs, discard items.
- Multi-stage world: Haunted Forest, Enchanted Castle, Bandit's Lair.
- Branching choices with at least 3 distinct endings.
- Error handling for invalid inputs, empty inventory, and zero-health states.

How to run:
- Requires Python 3.x and pygame.
- pip install pygame
- python combinedGame_finished.py
- To generate README.md: python combinedGame_finished.py --write-readme

Basic controls:
- Left/Right (A/D, ←/→): Move
- Up/Jump (W, ↑, Space): Jump
- J: Attack
- K: Dash
- T: Enter tactical combat (when near enemies)
- I: Open inventory
- B/F: During guide prompt, befriend (B) or fight (F)
- Esc: Quit
"""

# -------------------------
# Base imports and settings
# -------------------------
import pygame
import sys
import time
import random
import math
from pygame.locals import *
import argparse

# --- (Original settings preserved) ---
TITLE = "41 Water - Extended"
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

PIXEL_SCALE = 3
VIRTUAL_WIDTH = SCREEN_WIDTH // PIXEL_SCALE
VIRTUAL_HEIGHT = SCREEN_HEIGHT // PIXEL_SCALE

GRAVITY = 0.6
TERMINAL_VEL = 12

PLAYER_SPEED = 2.2
PLAYER_JUMP_SPEED = -9.0
PLAYER_WIDTH = 12
PLAYER_HEIGHT = 18

LEVEL_WIDTH = VIRTUAL_WIDTH * 3
LEVEL_HEIGHT = VIRTUAL_HEIGHT

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
UI_BG = (20, 20, 30)

KNOCKBACK_FORCE = 4
HITSTOP_DURATION = 0.1
INVINCIBILITY_DURATION = 0.6

TILE_SIZE = 16 * 3

# -------------------------
# Utility surfaces & sprites
# (reused / slightly adapted from original)
# -------------------------
def make_surface(w, h):
    return pygame.Surface((w, h), flags=pygame.SRCALPHA)

def scale_surface(surf):
    size = (max(1, surf.get_width() * PIXEL_SCALE), max(1, surf.get_height() * PIXEL_SCALE))
    return pygame.transform.scale(surf, size)

def generate_player_sprite(char_class="Wizard"):
    base_w, base_h = 12, 18
    idle = make_surface(base_w, base_h)
    attack = make_surface(base_w + 8, base_h)
    dash = make_surface(base_w, base_h)

    palettes = {
        "Wizard": ((60,40,120), (200,180,255)),
        "Worrier": ((120,50,40), (240,200,200)),
        "Warrior": ((120,50,40), (240,200,200))
    }
    main, accent = palettes.get(char_class, palettes["Wizard"])

    for x in range(base_w):
        for y in range(base_h):
            if 4 <= x <= 7 and 2 <= y <= 5:
                idle.set_at((x,y), (220,200,160))
            elif 3 <= x <= 8 and y >= 6:
                idle.set_at((x,y), main)
            elif 0 <= x <= base_w-1 and y >= base_h-3 and (x%2==0):
                idle.set_at((x,y), (max(0,main[0]-10), max(0,main[1]-10), max(0,main[2]-10)))

    idle.set_at((5,2), accent)
    idle.set_at((6,2), accent)

    aw = base_w + 8
    for x in range(aw):
        for y in range(base_h):
            if x < base_w:
                color = idle.get_at((x,y))
                try:
                    if color.a != 0:
                        attack.set_at((x,y), color)
                except Exception:
                    attack.set_at((x,y), color)
            else:
                weapon_x = x - base_w
                center = base_h // 2
                if char_class == "Wizard":
                    radius = 4
                    dx = weapon_x - 3
                    dy = y - center
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist <= radius:
                        intensity = 1 - (dist / radius)
                        r = min(255, int(240 * intensity))
                        g = min(255, int(140 * intensity))
                        b = min(255, int(40 * intensity))
                        attack.set_at((x,y), (r, g, b, int(255 * intensity)))

    for x in range(base_w):
        for y in range(base_h):
            color = idle.get_at((x,y))
            try:
                if color.a != 0:
                    dash.set_at((x,y), color)
                    if x < base_w-1:
                        dash.set_at((x+1,y), (min(255, color[0]+30), min(255,color[1]+30), min(255,color[2]+30)))
            except Exception:
                dash.set_at((x,y), color)

    return scale_surface(idle), scale_surface(attack), scale_surface(dash)

def generate_enemy_sprite(kind="grub"):
    w, h = 16, 16
    s = make_surface(w, h)
    # simplified procedural enemy art
    if kind == "grub":
        body = (80, 200, 140)
        for x in range(4, 12):
            for y in range(6, 11):
                s.set_at((x,y), body)
        s.set_at((9,7),(0,0,0))
    elif kind == "spider":
        body = (40,40,40)
        for x in range(5,11):
            for y in range(6,10):
                s.set_at((x,y), body)
        s.set_at((7,7),(255,0,0))
    else:
        for x in range(4,12):
            for y in range(6,11):
                s.set_at((x,y),(150,150,200))
    return scale_surface(s)

def generate_tile(tile_type="grass"):
    w, h = 16, 16
    t = make_surface(w, h)
    if tile_type == "grass":
        for x in range(w):
            for y in range(h):
                t.set_at((x,y), (60, 180, 80) if (x+y)%3 else (40,160,60))
    elif tile_type == "rock":
        for x in range(w):
            for y in range(h):
                t.set_at((x,y), (120,120,140))
    else:
        for x in range(w):
            for y in range(h):
                t.set_at((x,y), (40,40,60))
    return scale_surface(t)

# -------------------------
# LEVELS (renamed & flavored)
# -------------------------
LEVELS = []
LEVELS.append([
    # Haunted Forest (stage 1) - added flavor string in GameStateManager
    "........................................................................................",
    "........................................................................................",
    "...P....................................................................................",
    "........................................................................................",
    ".............GGG......................GGGG.....................GGG........................",
    "...........GGGGGGG...........GGGGGGGGGGGGG.................GGGGGGG......................",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
])

LEVELS.append([
    # Enchanted Castle (stage 2)
    "........................................................................................",
    "......................R..............................R....................................",
    "...........RRRRRRRRRRRRR..............R.................RRRRR...........................",
    "..................R...R.................................R.................................",
    ".......P................................................................................",
    "........................................................................................",
    "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR",
])

LEVELS.append([
    # Bandit's Lair (stage 3, final)
    "........................................................................................",
    "........................................................................................",
    "............GGGGGGG.......GGG....................P.............GGGGGGG..................",
    "........................................................................................",
    ".............GGGGGGGGG........GGGGGGG..........GGG.........GGGGGGGGG...................",
    "........................................................................................",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
    "GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",
])

def build_level_from_array(arr):
    tiles = []
    tile_surfaces = []
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

# -------------------------
# WorrySphere (kept)
# -------------------------
class WorrySphere:
    def __init__(self, x, y, max_radius=80, lifetime=1.2, damage=30, tick=0.25):
        self.x = x
        self.y = y
        self.created = time.time()
        self.lifetime = lifetime
        self.max_radius = max_radius
        self.damage = damage
        self.tick = tick
        self.last_tick = {}
        self.dead = False

    def age(self):
        return time.time() - self.created

    def progress(self):
        return min(1.0, max(0.0, self.age() / self.lifetime))

    def radius(self):
        return int(self.max_radius * self.progress())

    def update(self, enemies):
        if self.age() >= self.lifetime:
            self.dead = True
            return

        r = self.radius()
        if r <= 0:
            return

        for e in enemies:
            ex = e.rect.centerx
            ey = e.rect.centery
            dx = ex - self.x
            dy = ey - self.y
            if dx*dx + dy*dy <= r*r:
                now = time.time()
                last = self.last_tick.get(id(e), 0)
                if now - last >= self.tick:
                    e.take_damage(self.damage)
                    self.last_tick[id(e)] = now

    def draw(self, surf, camera_x=0, shake_y=0):
        r = self.radius()
        if r <= 0:
            return
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        alpha = int(200 * (1 - self.progress()))
        color = (255, 160, 180, alpha)
        pygame.draw.circle(s, color, (r, r), r)
        surf.blit(s, (self.x - r - camera_x, self.y - r + shake_y))

# -------------------------
# PLAYER (extended with RPG stats + inventory)
# -------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, char_class="Wizard"):
        super().__init__()
        self.char_class = char_class
        self.idle_surf, self.attack_surf, self.dash_surf = generate_player_sprite(char_class)
        self.image = self.idle_surf
        self.current_sprite = self.idle_surf
        self.rect = self.image.get_rect(topleft=(x,y))

        # movement
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.was_on_ground = False
        self.coyote_time = 0.1
        self.last_ground_time = 0

        # combat bits
        self.attacking = False
        self.attack_frame = 0
        self.spawn_protection = 2.0
        self.spawn_time = time.time()

        # visuals
        self.particles = []
        self.dash_particles = []

        self.dead = False
        self.facing = 1

        # base stats
        self.max_health = 100
        self.health = 100
        self.attack_cooldown = 0.4
        self.last_attack = -1.0
        self.attack_range = 28

        # dash
        self.can_dash = True
        self.dash_time = 0.18
        self.dashing = False
        self.dash_start = 0
        self.dash_speed = 8
        self.invulnerable = False
        self.last_dash_time = 0

        # RPG stats (Strength, Agility, Magic) — affect damage, dodge, spell power
        if char_class == "Wizard":
            self.max_health = 80
            self.health = 80
            self.strength = 6
            self.agility = 10
            self.magic = 18
            self.attack_cooldown = 0.45
            self.magic_power = 50
            self.defense = 12
            self.speed = 2.0
            self.special_ability = "Magic Shield"
        elif char_class == "Worrier":
            self.max_health = 120
            self.health = 120
            self.strength = 12
            self.agility = 8
            self.magic = 6
            self.attack_cooldown = 0.5
            self.magic_power = 10
            self.defense = 40
            self.speed = 1.8
            self.special_ability = "Worry Sphere"
        elif char_class == "Warrior":
            self.max_health = 140
            self.health = 140
            self.strength = 16
            self.agility = 6
            self.magic = 4
            self.attack_cooldown = 0.48
            self.magic_power = 5
            self.defense = 50
            self.speed = 1.6
            self.special_ability = "Shield Bash"
        else:
            # fallback balanced
            self.strength = 10
            self.agility = 10
            self.magic = 10
            self.magic_power = 10
            self.defense = 10
            self.speed = 2.0
            self.special_ability = "None"

        # progression / meta
        self.choice_points = 0
        self.lives = 3
        self.level = 1
        self.exp = 0

        # inventory
        self.inventory = []  # list of dict items {'id','name','type','effect','value'}
        self.equipped = {}  # e.g., 'ring': item

    def get_hitbox(self):
        return pygame.Rect(
            self.rect.left + 4,
            self.rect.top + 2,
            self.rect.width - 8,
            self.rect.height - 4
        )

    def move(self, dx):
        """Move left/right. Agility slightly affects movement responsiveness (flavor)."""
        speed_multiplier = 1.0 + (self.agility - 10) * 0.03  # small effect
        self.vx = dx * PLAYER_SPEED * speed_multiplier
        if dx != 0:
            self.facing = 1 if dx > 0 else -1

    def jump(self):
        now = time.time()
        if self.on_ground or (now - getattr(self, 'last_ground_time', 0) <= getattr(self, 'coyote_time', 0)):
            self.vy = PLAYER_JUMP_SPEED
            self.on_ground = False

    def start_dash(self):
        now = time.time()
        cooldown_progress = min(1.0, (now - getattr(self, 'last_dash_time', 0)) / 1.0)
        if not self.dashing and self.can_dash and cooldown_progress >= 1.0:
            self.dashing = True
            self.invulnerable = True
            self.dash_start = now
            self.last_dash_time = now
            self.can_dash = False
            # dash stats slightly influenced by agility
            base_speed = 8
            if self.char_class == "Wizard":
                self.dash_time = 0.15
                self.dash_speed = base_speed + 2 + int(self.agility * 0.05)
            elif self.char_class == "Worrier":
                self.dash_time = 0.25
                self.dash_speed = base_speed - 1 + int(self.agility * 0.03)
            elif self.char_class == "Warrior":
                self.dash_time = 0.18
                self.dash_speed = base_speed + int(self.strength * 0.05)

    def attack(self):
        """Start an action attack. Damage will be influenced by Strength/Magic."""
        now = time.time()
        if now - self.last_attack >= self.attack_cooldown:
            self.last_attack = now
            self.attacking = True
            self.attack_frame = 12
            # modify attack range / frames by class / agility
            if self.char_class == "Wizard":
                self.attack_range = 45
                self.attack_height = 16
                self.attack_frame = 15
            elif self.char_class == "Worrier":
                self.attack_range = 40
                self.attack_height = 80
                self.attack_frame = 12
            elif self.char_class == "Warrior":
                self.attack_range = 48
                self.attack_frame = 14
            return True
        return False

    def get_attack_hitbox(self):
        """Return the action attack hitbox (platformer)."""
        if not self.attacking or self.attack_frame <= 0:
            return None
        progress = self.attack_frame / 12.0
        if self.char_class == "Worrier":
            sphere_radius = int(self.attack_range * progress)
            return pygame.Rect(
                self.rect.centerx - sphere_radius,
                self.rect.centery - sphere_radius,
                sphere_radius * 2,
                sphere_radius * 2
            )
        elif self.char_class == "Warrior":
            reach = int(self.attack_range * (1.0 - progress + 0.2))
            height = int(self.rect.height * 0.6)
            y = self.rect.centery - height // 2
            if self.facing > 0:
                x = self.rect.right
            else:
                x = self.rect.left - reach
            return pygame.Rect(x, y, max(1, reach), height)
        else:
            width = int(self.attack_range * progress)
            if self.facing > 0:
                x = self.rect.right
            else:
                x = self.rect.left - width
            y = self.rect.centery - (getattr(self, 'attack_height', 16) // 2)
            height = getattr(self, 'attack_height', 16)
            return pygame.Rect(x, y, max(1, width), height)

    def update(self, dt, tiles):
        now = time.time()
        self.was_on_ground = self.on_ground
        self.on_ground = False

        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > TERMINAL_VEL:
                self.vy = TERMINAL_VEL

        # sprite selection
        if now - self.last_attack < 0.2:
            self.image = self.attack_surf
        elif self.dashing:
            self.image = self.dash_surf
        else:
            self.image = self.idle_surf

        if self.facing < 0:
            self.image = pygame.transform.flip(self.image, True, False)

        # dash movement
        if self.dashing:
            self.vx = self.facing * self.dash_speed
            if now - self.dash_start >= self.dash_time:
                self.dashing = False
                self.invulnerable = False
                self.can_dash = True
            # dash particles
            for _ in range(2):
                particle = {
                    'x': self.rect.centerx + random.randint(-5, 5),
                    'y': self.rect.centery + random.randint(-10, 10),
                    'life': 0.5,
                    'color': (200, 200, 255),
                    'size': random.randint(2, 4),
                    'created': now
                }
                self.dash_particles.append(particle)
        # cleanup particles
        self.dash_particles = [p for p in self.dash_particles if now - p['created'] < p['life']]

        # physics & tiles collisions
        self.rect.x += int(self.vx)
        self.resolve_collisions('x', tiles)
        self.rect.y += int(self.vy)
        self.resolve_collisions('y', tiles)

        if self.was_on_ground and not self.on_ground:
            self.last_ground_time = now

        if self.on_ground:
            self.can_dash = True

        if self.attacking:
            if self.attack_frame > 0:
                self.attack_frame -= 1
            else:
                self.attacking = False

        if not self.dashing:
            self.vx = 0

    def resolve_collisions(self, axis, tiles):
        for t in tiles:
            if self.rect.colliderect(t):
                if axis == 'x':
                    if self.vx > 0:
                        self.rect.right = t.left
                    elif self.vx < 0:
                        self.rect.left = t.right
                elif axis == 'y':
                    if self.vy > 0:
                        self.rect.bottom = t.top
                        self.on_ground = True
                        self.vy = 0
                    elif self.vy < 0:
                        self.rect.top = t.bottom
                        self.vy = 0

    def draw(self, surface, camera_x=0, shake_y=0):
        now = time.time()
        # dash particles
        for particle in self.dash_particles:
            particle_x = particle['x'] - camera_x
            if -particle['size'] <= particle_x <= VIRTUAL_WIDTH:
                life_progress = (now - particle['created']) / particle['life']
                alpha = int(255 * (1 - life_progress))
                for i in range(3):
                    trail_x = particle_x - (i * 2 * self.facing)
                    trail_alpha = alpha // (i + 1)
                    trail_surf = pygame.Surface((particle['size'], particle['size']))
                    trail_surf.fill(particle['color'])
                    trail_surf.set_alpha(trail_alpha)
                    surface.blit(trail_surf, (trail_x, particle['y'] + shake_y))

        draw_pos = (self.rect.x - camera_x, self.rect.y + shake_y)
        base_image = self.image.copy()

        if not self.attacking and not self.dashing:
            if self.char_class == "Wizard" and random.random() < 0.06:
                sparkle_x = draw_pos[0] + random.randint(-5, self.rect.width + 5)
                sparkle_y = draw_pos[1] + random.randint(-5, self.rect.height + 5)
                sparkle_size = random.randint(1, 3)
                sparkle_surf = pygame.Surface((sparkle_size, sparkle_size))
                sparkle_surf.fill((200, 200, 255))
                sparkle_surf.set_alpha(random.randint(100, 200))
                surface.blit(sparkle_surf, (sparkle_x, sparkle_y))

        surface.blit(base_image, draw_pos)

        # show attack overlay for action-mode
        if self.attacking and self.attack_frame > 0:
            progress = self.attack_frame / 12.0
            if self.char_class == "Worrier":
                sphere_radius = int(self.attack_range * progress)
                center_x = draw_pos[0] + self.rect.width//2
                center_y = self.rect.centery
                ring_radius = max(8, sphere_radius)
                ring_surf = pygame.Surface((ring_radius*2+4, ring_radius*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (255, 180, 180, 120), (ring_radius+2, ring_radius+2), ring_radius, 2)
                surface.blit(ring_surf, (center_x - ring_radius - 2, center_y - ring_radius - 2))
            else:
                attack_width = int(self.attack_range * progress)
                attack_height = 20 + int(10 * (1 - progress))
                if self.facing > 0:
                    attack_x = (self.rect.right - camera_x)
                else:
                    attack_x = (self.rect.left - attack_width - camera_x)
                alpha_surf = pygame.Surface((max(1, attack_width), attack_height), pygame.SRCALPHA)
                alpha_surf.fill((100, 100, 255, 120))
                surface.blit(alpha_surf, (attack_x, self.rect.centery - attack_height//2))

        # cooldown indicator (dash)
        now = time.time()
        cooldown_progress = min(1.0, (now - getattr(self, 'last_dash_time', 0)) / 1.0)
        if cooldown_progress < 1.0:
            indicator_radius = 10
            center_x = draw_pos[0] + self.rect.width // 2
            center_y = draw_pos[1] - indicator_radius - 4
            pygame.draw.circle(surface, (40,40,40), (center_x, center_y), indicator_radius)
            start_angle = -90
            end_angle = start_angle + (360 * (1 - cooldown_progress))
            if end_angle != start_angle:
                pygame.draw.arc(surface, (200,200,255), (center_x - indicator_radius, center_y - indicator_radius, indicator_radius*2, indicator_radius*2),
                                math.radians(start_angle), math.radians(end_angle), 3)

    # -----------------------
    # Inventory methods
    # -----------------------
    def add_item(self, item):
        """Add item dict to inventory"""
        if item is None: return
        self.inventory.append(item)

    def list_inventory(self):
        """Return list-friendly representation"""
        return [f"{i+1}. {it['name']} ({it['type']})" for i, it in enumerate(self.inventory)]

    def use_item(self, index):
        """Use item by index (0-based). Returns (success,message)."""
        if index < 0 or index >= len(self.inventory):
            return False, "Invalid item index."
        item = self.inventory.pop(index)
        t = item.get('type')
        if t == 'potion':
            heal = item.get('value', 20)
            self.health = min(self.max_health, self.health + heal)
            return True, f"Used {item['name']}. Restored {heal} HP."
        elif t == 'buff_strength':
            bonus = item.get('value', 5)
            self.strength += bonus
            # buff is permanent in this simplified version
            return True, f"{item['name']} equipped. Strength +{bonus}."
        elif t == 'key':
            return True, f"Used {item['name']} (story item)."
        else:
            return False, f"Item {item['name']} had no effect."

    def discard_item(self, index):
        if index < 0 or index >= len(self.inventory):
            return False, "Invalid index."
        item = self.inventory.pop(index)
        return True, f"Discarded {item['name']}."

# -------------------------
# ENEMY (kept with minor adjustments)
# -------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="grub"):
        super().__init__()
        self.surf = generate_enemy_sprite(kind)
        self.image = self.surf
        self.rect = self.image.get_rect(topleft=(x,y))
        self.kind = kind

        self.vx = random.choice([-1, 1]) * 0.6
        self.vy = 0
        self.on_ground = False
        self.dead = False

        self.last_hurt = 0
        self.last_attack = -2.0
        self.attacking = False
        self.attack_frame = 0

        # AI params
        self.decision_timer = 0
        self.decision_interval = random.uniform(0.5, 2.0)
        self.aggression = random.uniform(0.4, 0.8)
        self.confidence = random.uniform(0.5, 1.0)
        self.hit_particles = []

        # basic stats by kind
        if kind == "grub":
            self.max_health = 30
            self.health = self.max_health
            self.speed = 0.8
            self.damage = 8
            self.attack_range = 45
            self.attack_cooldown = 2.0
        elif kind == "spider":
            self.max_health = 25
            self.health = self.max_health
            self.speed = 1.4
            self.damage = 12
            self.attack_range = 70
            self.attack_cooldown = 1.8
        elif kind == "slime":
            self.max_health = 40
            self.health = self.max_health
            self.speed = 0.7
            self.damage = 10
            self.attack_range = 35
            self.attack_cooldown = 2.2
        elif kind == "ghost":
            self.max_health = 28
            self.health = self.max_health
            self.speed = 1.1
            self.damage = 14
            self.attack_range = 55
            self.attack_cooldown = 1.9
        else:
            self.max_health = 20
            self.health = 20
            self.speed = 1.0
            self.damage = 6
            self.attack_range = 40
            self.attack_cooldown = 2.0

        self.level = 1
        self.exp_value = 5 * self.level

    def update(self, tiles, player_rect=None):
        now = time.time()
        attacked_flag = False

        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 220:
                # simple chase
                self.vx = math.copysign(self.speed, dx)
            if dist <= self.attack_range and now - self.last_attack >= self.attack_cooldown:
                attack_chance = self.aggression + (1 - (self.health / max(1, self.max_health))) * 0.3
                if random.random() < attack_chance:
                    self.attacking = True
                    self.last_attack = now
                    self.attack_frame = 10
                    attacked_flag = True

        # movement
        self.rect.x += int(self.vx)
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vx > 0:
                    self.rect.right = t.left
                else:
                    self.rect.left = t.right
                self.vx *= -0.8

        # gravity
        if not self.on_ground:
            self.vy += 0.7
        self.vy = min(self.vy, 12)
        self.rect.y += int(self.vy)
        self.on_ground = False
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vy > 0:
                    self.rect.bottom = t.top
                    self.on_ground = True
                    self.vy = 0
                else:
                    self.rect.top = t.bottom
                    self.vy = 0

        if self.attacking:
            self.attack_frame -= 1
            if self.attack_frame <= 0:
                self.attacking = False

        if self.health <= 0:
            self.dead = True

        # update particles
        for p in list(self.hit_particles):
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 0.05
            if p['life'] <= 0:
                try:
                    self.hit_particles.remove(p)
                except Exception:
                    pass

        return attacked_flag

    def take_damage(self, damage):
        now = time.time()
        if now - self.last_hurt < 0.12:
            return
        self.last_hurt = now
        self.health -= damage
        # spawn simple hit particles
        for _ in range(4):
            angle = random.uniform(0, math.pi*2)
            sp = {
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'vx': math.cos(angle)*random.uniform(1,3),
                'vy': math.sin(angle)*random.uniform(1,3),
                'life': 0.5,
                'color': (255,200,200)
            }
            self.hit_particles.append(sp)

    def draw(self, surf, camera_x, shake_y=0):
        draw_pos = (self.rect.x - camera_x, self.rect.y + shake_y)
        base_image = self.image.copy()
        now = time.time()
        if now - self.last_hurt < 0.25:
            flash = base_image.copy()
            flash.fill((255,255,255))
            flash.set_alpha(150)
            surf.blit(flash, draw_pos)
        surf.blit(base_image, draw_pos)

        # draw HP bar
        health_width = 20
        health_height = 3
        bar_y = draw_pos[1] - 6
        pygame.draw.rect(surf, (80,80,80), (draw_pos[0], bar_y, health_width, health_height))
        health_percent = max(0.0, self.health / max(1, self.max_health))
        bar_color = (100,255,100) if health_percent > 0.5 else (255,255,80) if health_percent > 0.2 else (255,100,100)
        pygame.draw.rect(surf, bar_color, (draw_pos[0], bar_y, int(health_width * health_percent), health_height))

        # draw hit particles
        for p in list(self.hit_particles):
            alpha = int(255 * (p['life'] / 0.5))
            surf_s = pygame.Surface((3,3), pygame.SRCALPHA)
            surf_s.fill((p['color'][0], p['color'][1], p['color'][2], alpha))
            surf.blit(surf_s, (int(p['x'] - camera_x), int(p['y'] + shake_y)))

# -------------------------
# Boss (kept)
# -------------------------
class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 64)
        self.health = 200
        self.vx = 0
        self.vy = 0
        self.attack_timer = 0
        self.attack_cooldown = 1.5
        self.dead = False
        self.color = (150, 50, 50)

    def update(self, tiles, player_rect):
        if self.dead:
            return
        dx = player_rect.centerx - self.rect.centerx
        self.vx = 2 if dx > 0 else -2
        if random.random() < 0.02:
            self.vy = -10
        self.vy += 0.5
        self.rect.x += self.vx
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vx > 0:
                    self.rect.right = tile.left
                else:
                    self.rect.left = tile.right
                self.vx = 0
        self.rect.y += self.vy
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vy > 0:
                    self.rect.bottom = tile.top
                    self.vy = 0
                else:
                    self.rect.top = tile.bottom
                    self.vy = 1

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.dead = True

    def draw(self, surface, camera_x, shake_y=0):
        if not self.dead:
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_x
            draw_rect.y += shake_y
            pygame.draw.rect(surface, self.color, draw_rect)
            health_rect = pygame.Rect(self.rect.x - camera_x, self.rect.y - 10 + shake_y,
                                     self.rect.width * max(0.0, self.health / 200), 5)
            pygame.draw.rect(surface, (255, 0, 0), health_rect)

# -------------------------
# UI & HUD
# -------------------------
pygame.font.init()
FONT = pygame.font.SysFont("consolas", 12)
BIG_FONT = pygame.font.SysFont("consolas", 20)

def draw_hud(surf, player, stage, guide_text=None, lives=None):
    pygame.draw.rect(surf, UI_BG, (2, 2, 260, 110))
    class_text = FONT.render(f"{player.char_class} - Stage: {stage}", True, WHITE)
    surf.blit(class_text, (6, 6))
    if lives is not None:
        lives_text = FONT.render(f"Lives: {lives}", True, WHITE)
        surf.blit(lives_text, (200, 6))
    # HP bar
    health_percent = player.health / max(1, player.max_health)
    pygame.draw.rect(surf, (60, 0, 0), (6, 26, 120, 10))
    pygame.draw.rect(surf, (200, 0, 0), (6, 26, int(120 * health_percent), 10))
    hp_text = FONT.render(f"HP: {player.health}/{player.max_health}", True, WHITE)
    surf.blit(hp_text, (130, 24))
    # stats
    y = 42
    stats = [
        f"STR: {player.strength}",
        f"AGI: {player.agility}",
        f"MAG: {player.magic}",
        f"Spc: {player.special_ability}"
    ]
    for s in stats:
        surf.blit(FONT.render(s, True, WHITE), (6, y))
        y += 12
    if guide_text:
        # small guide box
        box_h = 36
        w = surf.get_width()
        pygame.draw.rect(surf, UI_BG, (2, surf.get_height() - box_h - 2, w - 4, box_h))
        surf.blit(FONT.render(guide_text, True, WHITE), (6, surf.get_height() - box_h + 6))

# -------------------------
# Tactical (turn-based) combat overlay
# -------------------------
class TacticalCombat:
    """
    A simple turn-based combat overlay. When started, it runs a separate loop
    until combat finishes. Combat entities:
    - Player (uses player's stats)
    - A small list of enemy dicts: {'name','hp','atk','def','agi','kind'}
    """
    def __init__(self, screen_surface, player, enemies, on_finish_callback):
        self.screen = screen_surface
        self.player = player
        # convert first N enemies to tactical enemies
        self.enemies = []
        for e in enemies[:4]:  # only up to 4 enemies for tactical
            kind = e.kind
            hp = max(10, int(e.max_health * (1 + random.uniform(-0.1,0.2))))
            atk = max(3, int(e.damage * (1 + random.uniform(-0.2,0.3))))
            agi = max(1, int(random.uniform(4, 8)))
            self.enemies.append({'name': kind, 'hp': hp, 'atk': atk, 'def': 2, 'agi': agi, 'source': e})
        self.on_finish = on_finish_callback
        self.state = "player_turn"  # player_turn, enemies_turn, finished
        self.message = "Tactical Combat started. Choose an action."
        # turn order based on agility
        self.turn_order = []
        self.generate_turn_order()
        self.selected_option = 0
        self.options = ["Attack", "Defend", "Magic", "Item", "Flee"]
        self.log = []
        self.running = True
        # store original positions / action
        self.player_temp_hp = self.player.health
        self.player_defending = False

    def generate_turn_order(self):
        entries = []
        pid = ('player', self.player.agility)
        entries.append(pid)
        for i, e in enumerate(self.enemies):
            entries.append((i, e['agi']))
        # sort descending agility
        entries.sort(key=lambda x: x[1], reverse=True)
        self.turn_order = [ent[0] for ent in entries]

    def roll_hit(self, atk, defn):
        # dice-roll influenced
        roll = random.randint(1, 20) + int(atk * 0.5)
        threshold = 8 + defn
        return roll >= threshold

    def player_attack(self, target_index):
        # Attack with strength (plus minor randomness)
        target = self.enemies[target_index]
        base_atk = max(1, int(self.player.strength + random.randint(-2, 3)))
        if self.roll_hit(base_atk, target['def']):
            dmg = base_atk + random.randint(0, int(self.player.strength * 0.5))
            target['hp'] -= dmg
            self.log.append(f"You hit {target['name']} for {dmg}.")
        else:
            self.log.append("Your attack missed.")

    def player_magic(self, target_index):
        # Magic uses magic stat and magic_power; Wizard stronger
        target = self.enemies[target_index]
        power = int(self.player.magic * 1.5) + int(self.player.magic_power * 0.1)
        # randomness/dice
        if random.random() < 0.9:
            dmg = power + random.randint(-2, power//4)
            target['hp'] -= dmg
            self.log.append(f"You cast a spell on {target['name']} for {dmg}.")
        else:
            self.log.append("Spell fizzled.")

    def enemy_action(self, idx):
        e = self.enemies[idx]
        if e['hp'] <= 0:
            return
        # choose target (player only)
        # simple hit check
        if self.roll_hit(e['atk'], int(self.player.defense * 0.1)):
            dmg = e['atk'] + random.randint(0, e['atk']//2)
            if self.player_defending:
                dmg = max(0, dmg - int(self.player.defense * 0.3))
            self.player.health -= dmg
            self.log.append(f"{e['name']} hits you for {dmg}.")
        else:
            self.log.append(f"{e['name']}'s attack missed.")

    def cleanup_dead(self):
        # remove dead enemies
        self.enemies = [e for e in self.enemies if e['hp'] > 0]

    def update(self):
        # Check for finished states
        if self.player.health <= 0:
            self.running = False
            self.state = "finished"
            self.message = "You were defeated..."
            self.on_finish(False, self.log)
            return

        self.cleanup_dead()
        if len(self.enemies) == 0:
            self.running = False
            self.state = "finished"
            self.message = "Victory!"
            # reward: small XP and items; we call on_finish with True
            self.on_finish(True, self.log)
            return

    def draw(self):
        # Draw a compact tactical UI on top of the screen
        surf = self.screen
        w = surf.get_width()
        h = surf.get_height()
        # darken background
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 190))
        surf.blit(overlay, (0,0))

        # draw enemy panels
        ex = 20
        ey = 20
        for i, e in enumerate(self.enemies):
            box = pygame.Rect(ex + i*120, ey, 110, 60)
            pygame.draw.rect(surf, (60,60,80), box)
            surf.blit(FONT.render(f"{e['name']}", True, WHITE), (box.x+4, box.y+4))
            surf.blit(FONT.render(f"HP: {e['hp']}", True, WHITE), (box.x+4, box.y+22))

        # draw player panel
        pbox = pygame.Rect(20, 100, 300, 80)
        pygame.draw.rect(surf, (60,60,80), pbox)
        surf.blit(FONT.render("You:", True, WHITE), (pbox.x+4, pbox.y+4))
        surf.blit(FONT.render(f"HP: {self.player.health}", True, WHITE), (pbox.x+4, pbox.y+22))
        surf.blit(FONT.render(f"STR:{self.player.strength} AGI:{self.player.agility} MAG:{self.player.magic}", True, WHITE), (pbox.x+4, pbox.y+40))

        # options
        opt_box = pygame.Rect(20, 190, 340, 120)
        pygame.draw.rect(surf, (40,40,60), opt_box)
        surf.blit(FONT.render("Actions (Left/Right to change, Enter to select):", True, WHITE), (opt_box.x+6, opt_box.y+6))
        for i, o in enumerate(self.options):
            col = (255,255,120) if i == self.selected_option else (200,200,200)
            surf.blit(BIG_FONT.render(o, True, col), (opt_box.x + 6 + i*64, opt_box.y + 36))

        # message log (last few)
        ly = 330
        for i, m in enumerate(self.log[-6:]):
            surf.blit(FONT.render(m, True, (220,220,220)), (20, ly + i*14))

    def handle_input(self, events):
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_LEFT:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif e.key == K_RIGHT:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif e.key == K_ESCAPE:
                    # allow leaving tactical combat (attempt flee)
                    self.running = False
                    self.on_finish(False, ["You fled tactical combat."])
                elif e.key == K_RETURN:
                    sel = self.options[self.selected_option]
                    # ensure at least one enemy exists
                    if len(self.enemies) == 0:
                        self.log.append("No enemies to act upon.")
                        return
                    target_index = 0  # default target first enemy (could be expanded)
                    if sel == "Attack":
                        self.player_attack(target_index)
                    elif sel == "Defend":
                        self.player_defending = True
                        self.log.append("You brace for incoming attacks.")
                    elif sel == "Magic":
                        self.player_magic(target_index)
                    elif sel == "Item":
                        # auto-use first potion if exists
                        used = False
                        for i, it in enumerate(self.player.inventory):
                            if it['type'] == 'potion':
                                ok, msg = self.player.use_item(i)
                                self.log.append(msg)
                                used = True
                                break
                        if not used:
                            self.log.append("No usable potions.")
                    elif sel == "Flee":
                        if random.random() < 0.4 + self.player.agility * 0.02:
                            self.running = False
                            self.on_finish(False, ["You successfully fled."])
                            return
                        else:
                            self.log.append("Failed to flee.")
                    # next: enemies' turn after player acts
                    self.player_defending = False
                    # enemies act
                    for idx in range(len(self.enemies)):
                        if self.enemies[idx]['hp'] > 0:
                            # enemy attacks
                            if random.random() < 0.9:
                                self.enemy_action(idx)
                    # remove dead enemies and continue
                    self.cleanup_dead()
                    self.update()

# -------------------------
# GameStateManager (integrated; handles inventory, world, branches)
# -------------------------
class GameStateManager:
    def __init__(self, screen):
        self.screen = screen
        self.stage_index = 0
        self.stage_names = ["Haunted Forest", "Enchanted Castle", "Bandit's Lair"]
        self.player = None
        self.enemies = []
        self.boss = None
        self.tiles = []
        self.tile_surfaces = []
        self.guide_text = "Welcome, traveler. Let's find 41 Water."
        self.guide_help_count = 0

        self.guide_present = False
        self.guide_pos = (0, 0)
        self.cutscene_active = False
        self.cutscene_end_time = 0
        self.guide_betrayed = False
        self.ending = None

        self.camera_x = 0
        self.camera_y = 0
        self.level_width = LEVEL_WIDTH
        self.level_height = LEVEL_HEIGHT

        self.lives = 3
        self.respawn_delay = 2.0
        self.respawn_time = None
        self.spawn_point = (32, 32)

        self.checkpoints = []

        self.fade_state = None
        self.fade_start = 0
        self.fade_duration = 1.0

        self.screen_shake = 0
        self.hitstop_until = 0
        self.damage_numbers = []

        self.worry_spheres = []
        self.items_on_ground = []  # world items (dict with rect + item)

        # spawn & enemy management
        self.enemies_to_defeat = 8
        self.enemies_defeated = 0
        self.max_enemies = 8
        self.last_spawn_time = time.time()
        self.spawn_cooldown = 2.0

    def start_new(self, char_class):
        self.stage_index = 0
        self.load_stage(self.stage_index, char_class)

    def load_stage(self, idx, char_class):
        arr = LEVELS[idx]
        tiles, tile_surfaces = build_level_from_array(arr)
        self.tiles = tiles
        self.tile_surfaces = tile_surfaces

        spawn = None
        for y, row in enumerate(arr):
            for x, ch in enumerate(row):
                if ch == "P":
                    spawn = (x * TILE_SIZE, y * TILE_SIZE)
        if spawn is None:
            spawn = (32, 32)

        if self.player is None:
            self.player = Player(spawn[0], spawn[1], char_class)
            self.player.lives = self.lives
        else:
            self.player.rect.topleft = spawn
            self.player.vx = self.player.vy = 0

        self.spawn_point = spawn
        self.camera_x = max(0, min(spawn[0] - VIRTUAL_WIDTH // 2, self.level_width - VIRTUAL_WIDTH))

        # checkpoints
        self.checkpoints = []
        checkpoint_xs = [int(self.level_width * 0.33), int(self.level_width * 0.66)]
        for cx in checkpoint_xs:
            spawn_y = None
            for t in self.tiles:
                if t.left <= cx <= t.right:
                    if spawn_y is None or t.top < spawn_y:
                        spawn_y = t.top
            if spawn_y is None:
                spawn_y = VIRTUAL_HEIGHT - TILE_SIZE * 2
            cp_rect = pygame.Rect(cx - 8, spawn_y - TILE_SIZE, 16, TILE_SIZE)
            self.checkpoints.append({'rect': cp_rect, 'activated': False})

        # reset enemies/items
        self.enemies = []
        self.items_on_ground = []
        self.spawn_initial_enemies()

        # stage story / guide presence
        stage_story = {
            0: "Haunted Forest: Strange creatures guard the path to 41 Water.",
            1: "Enchanted Castle: The halls hold secrets and tests of will.",
            2: "Bandit's Lair: This is where choices matter."
        }
        self.guide_text = stage_story.get(idx, "Keep moving forward...")

        if idx == 2:
            # final stage: guide appears
            self.boss = None
            self.guide_present = True
            gp_x = int(self.level_width * 0.5)
            gp_y = VIRTUAL_HEIGHT - TILE_SIZE * 3
            self.guide_pos = (gp_x, gp_y)
            self.guide_betrayed = False
        else:
            self.boss = None
            self.guide_present = False

        # goal numbers scale
        self.enemies_to_defeat = 6 + idx * 3
        self.enemies_defeated = 0
        self.max_enemies = 6 + idx * 2

        self.worry_spheres = []

    def spawn_initial_enemies(self):
        for i in range(3):
            self.try_spawn_enemy(force=True)

    def try_spawn_enemy(self, force=False):
        now = time.time()
        if (not force) and (now - self.last_spawn_time < self.spawn_cooldown or len(self.enemies) >= self.max_enemies):
            return
        # spawn ahead of camera random
        spawn_left = int(self.camera_x + VIRTUAL_WIDTH + 16)
        spawn_right = int(min(spawn_left + (VIRTUAL_WIDTH // 2), LEVEL_WIDTH - 100))
        if spawn_left >= spawn_right:
            spawn_left = int(VIRTUAL_WIDTH * 0.7)
            spawn_right = int(LEVEL_WIDTH * 0.9)
        attempts = 0
        while attempts < 10:
            ex = random.randint(spawn_left, spawn_right)
            ey = random.randint(40, int(VIRTUAL_HEIGHT * 0.7))
            spawn_rect = pygame.Rect(ex, ey, 32, 32)
            collides = False
            for t in self.tiles:
                if spawn_rect.colliderect(t):
                    collides = True
                    break
            if collides:
                attempts += 1
                continue
            enemy_kind = random.choice(["grub","grub","spider","slime"] if self.stage_index==0 else ["spider","slime","ghost"])
            ent = Enemy(ex, ey, kind=enemy_kind)
            self.enemies.append(ent)
            self.last_spawn_time = now
            return
        return

    def update(self, dt, inputs, events):
        now = time.time()
        # hitstop handling
        if now < self.hitstop_until:
            return

        # screen shake decay
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - 0.4)

        # death & respawn handling
        if getattr(self.player, 'health', 999) <= 0:
            if self.respawn_time is None:
                self.lives -= 1
                self.respawn_time = now + self.respawn_delay
                self.fade_state = 'out'
                self.fade_start = now
                self.fade_duration = self.respawn_delay
                self.player.dead = True
                self.player.vx = self.player.vy = 0
                self.player.rect.topleft = (-1000, -1000)
                if self.lives < 0:
                    self.ending = "Defeat - You couldn't find 41 Water"
                    return
            else:
                if now < self.respawn_time:
                    return
                # respawn
                self.respawn_time = None
                self.player.dead = False
                self.player.health = self.player.max_health
                self.player.rect.topleft = self.spawn_point
                self.player.spawn_time = now
                self.player.invulnerable = True
                self.fade_state = 'in'
                self.fade_start = now
                self.fade_duration = 0.8

        # platform inputs
        if inputs.get("left"): self.player.move(-1)
        elif inputs.get("right"): self.player.move(1)
        else: self.player.move(0)
        if inputs.get("jump"): self.player.jump()
        if inputs.get("dash"): self.player.start_dash()

        # tactical combat activation (press T)
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_t:
                    # check proximity to at least one enemy
                    near = [en for en in self.enemies if abs(en.rect.centerx - self.player.rect.centerx) < 160]
                    if near:
                        # start tactical combat overlay
                        def on_finish(victory, log):
                            # reward on victory
                            if victory:
                                # convert defeated tactical enemies into drops and XP
                                self.player.exp += 10 * (1 + self.stage_index)
                                # small item drop chance
                                if random.random() < 0.6:
                                    it = random.choice([{'id':'potion','name':'Minor Potion','type':'potion','value':30},
                                                        {'id':'ring','name':'Ring of Strength','type':'buff_strength','value':2},
                                                        {'id':'key','name':'Rusty Key','type':'key','value':0}])
                                    self.player.add_item(it)
                            else:
                                # on failure or flee, small penalty / message
                                self.player.health = max(1, self.player.health - 5)
                                self.guide_text = "Tactical combat ended."
                        tactical = TacticalCombat(self.screen, self.player, near, on_finish)
                        # block main loop until tactical completes - simple modal loop
                        clock = pygame.time.Clock()
                        while tactical.running:
                            tevents = pygame.event.get()
                            for ce in tevents:
                                if ce.type == QUIT:
                                    pygame.quit()
                                    sys.exit()
                            tactical.handle_input(tevents)
                            tactical.draw()
                            pygame.display.flip()
                            tactical.update()
                            clock.tick(30)
                        # remove any enemy objects that got defeated in the tactical conversion
                        for en in near:
                            if en.dead or en.health <= 0:
                                try:
                                    self.enemies.remove(en)
                                except ValueError:
                                    pass
                        # continue game after tactical
                if e.key == K_i:
                    # open inventory modal
                    self.open_inventory_modal()
                if e.key == K_b and self.stage_index == 2 and self.guide_present:
                    # befriend guide
                    self.guide_help_count += 2
                    self.guide_text = "You befriend the guide. They seem grateful."
                    self.guide_present = False
                    self.player.choice_points += 2
                if e.key == K_f and self.stage_index == 2 and self.guide_present:
                    # fight guide (branch)
                    self.guide_text = "You attack the guide. They will not forget..."
                    self.guide_present = False
                    self.guide_betrayed = True
                    self.player.choice_points -= 1

        # update player physics
        self.player.update(dt, self.tiles)

        # checkpoint activation
        for cp in self.checkpoints:
            if not cp['activated'] and self.player.rect.colliderect(cp['rect']):
                cp['activated'] = True
                cp['activation_time'] = time.time()
                self.spawn_point = (cp['rect'].x, cp['rect'].y - TILE_SIZE)
                self.guide_text = "Checkpoint reached. Your progress is saved."

        # camera update & spawns
        self.update_camera()
        self.try_spawn_enemy()

        # handle enemy AI & collisions
        has_protection = (now - getattr(self.player, 'spawn_time', 0)) < getattr(self.player, 'spawn_protection', 0)
        for e in list(self.enemies):
            attacked = e.update(self.tiles, self.player.rect)
            if attacked:
                attack_rect = e.get_attack_rect() if hasattr(e, 'get_attack_rect') else None
                if attack_rect and attack_rect.colliderect(self.player.rect) and not has_protection:
                    # damage calculation uses enemy.damage and player's defense and agility as dodge chance
                    dodge_chance = max(0.0, min(0.6, self.player.agility * 0.01))
                    if random.random() > dodge_chance:
                        self.player.health -= e.damage
                        self.trigger_hitstop(0.06)
                        self.add_screen_shake(3)
                        # spawn damage number
                        self.spawn_damage_number(self.player.rect.centerx, self.player.rect.top, e.damage, (255,100,100))
                    else:
                        self.spawn_damage_number(self.player.rect.centerx, self.player.rect.top, 0, (200,200,200))
            # if enemy died, make an item drop
            if getattr(e, 'dead', False):
                # small drop chance
                if random.random() < 0.5:
                    drop = random.choice([
                        {'id':'potion','name':'Minor Potion','type':'potion','value':25},
                        {'id':'potion','name':'Tiny Potion','type':'potion','value':15},
                        {'id':'ring','name':'Rusty Ring','type':'buff_strength','value':1}
                    ])
                    r = pygame.Rect(e.rect.centerx, e.rect.centery, 8, 8)
                    self.items_on_ground.append({'rect': r, 'item': drop, 'created': time.time()})
                try:
                    self.enemies.remove(e)
                    self.enemies_defeated += 1
                except Exception:
                    pass

        # pickup items on ground
        for it in list(self.items_on_ground):
            if self.player.rect.colliderect(it['rect']):
                self.player.add_item(it['item'])
                self.items_on_ground.remove(it)
                self.guide_text = f"Picked up {it['item']['name']}."
        # game progression: edge of level -> advance or final endings
        edge_threshold = self.level_width - 60
        if (self.player.rect.right >= edge_threshold or
            (self.player.dashing and self.player.rect.right + (self.player.dash_speed * self.player.facing) >= edge_threshold)):
            if self.enemies_defeated >= self.enemies_to_defeat and not self.boss:
                advanced = self.advance_stage_or_end()
                if advanced:
                    return

        # boss update if present
        if self.boss:
            self.boss.update(self.tiles, self.player.rect)

        # worry spheres
        for ws in list(getattr(self, 'worry_spheres', [])):
            ws.update(self.enemies)
            if ws.dead:
                try:
                    self.worry_spheres.remove(ws)
                except Exception:
                    pass

        # guide proximity triggers
        if self.stage_index == 2 and self.guide_present and not self.cutscene_active and not self.guide_betrayed:
            gx = getattr(self, 'guide_pos', (self.level_width//2, 0))[0]
            if abs(self.player.rect.centerx - gx) < 96:
                self.start_betrayal_cutscene()

        if self.cutscene_active:
            if time.time() >= self.cutscene_end_time:
                self.cutscene_active = False
                self.guide_text = "The guide offers you a choice: befriend (B) or oppose (F)."
            else:
                return

    # -------------------------
    # Inventory modal
    # -------------------------
    def open_inventory_modal(self):
        # modal display: left/right to select item, U use, D discard, Esc exit
        clock = pygame.time.Clock()
        sel = 0
        message = ""
        while True:
            evs = pygame.event.get()
            for e in evs:
                if e.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == KEYDOWN:
                    if e.key == K_ESCAPE:
                        return
                    if e.key == K_LEFT:
                        sel = max(0, sel-1)
                    if e.key == K_RIGHT:
                        sel = min(max(0, len(self.player.inventory)-1), sel+1)
                    if e.key == K_u:  # use
                        if len(self.player.inventory) == 0:
                            message = "Inventory is empty."
                        else:
                            ok, msg = self.player.use_item(sel)
                            message = msg
                            sel = min(sel, max(0, len(self.player.inventory)-1))
                    if e.key == K_d:  # discard
                        if len(self.player.inventory) == 0:
                            message = "Inventory is empty."
                        else:
                            ok, msg = self.player.discard_item(sel)
                            message = msg
                            sel = min(sel, max(0, len(self.player.inventory)-1))
            # draw modal
            s = self.screen
            overlay = pygame.Surface((s.get_width(), s.get_height()), pygame.SRCALPHA)
            overlay.fill((10,10,20,200))
            s.blit(overlay, (0,0))
            # title
            s.blit(BIG_FONT.render("Inventory (Use: U, Discard: D, Esc: Exit)", True, WHITE), (20,20))
            if len(self.player.inventory) == 0:
                s.blit(FONT.render("Inventory is empty.", True, (220,220,220)), (20,70))
            else:
                # show selected item and list
                show_y = 70
                for i, it in enumerate(self.player.inventory):
                    col = (255,255,120) if i == sel else (200,200,200)
                    s.blit(FONT.render(f"{i+1}. {it['name']} ({it['type']})", True, col), (20, show_y + i*18))
                # show details of selected
                it = self.player.inventory[sel] if sel < len(self.player.inventory) else None
                if it:
                    s.blit(FONT.render(f"Selected: {it['name']} - {it.get('type')}", True, WHITE), (420, 70))
                    s.blit(FONT.render(f"Desc: value={it.get('value','-')}", True, WHITE), (420, 94))
            # message area
            s.blit(FONT.render(message, True, (200,200,120)), (20, s.get_height()-40))
            pygame.display.flip()
            clock.tick(30)

    def update_camera(self):
        target_x = self.player.rect.centerx - VIRTUAL_WIDTH // 2
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_x = max(0, min(self.camera_x, self.level_width - VIRTUAL_WIDTH))
        if self.player.rect.left < self.camera_x + 20:
            self.player.rect.left = self.camera_x + 20
            self.player.vx = max(0, self.player.vx)

    def draw(self, surf):
        surf.fill((40,50,70))
        self.update_camera()
        shake_x = random.randint(-int(self.screen_shake), int(self.screen_shake)) if self.screen_shake > 0 else 0
        shake_y = random.randint(-int(self.screen_shake), int(self.screen_shake)) if self.screen_shake > 0 else 0
        camera_with_shake = self.camera_x - shake_x

        # tiles
        for tile_surf, pos in self.tile_surfaces:
            camera_adjusted_pos = (pos[0] - camera_with_shake, pos[1] + shake_y)
            if -tile_surf.get_width() <= camera_adjusted_pos[0] <= VIRTUAL_WIDTH:
                surf.blit(tile_surf, camera_adjusted_pos)

        # checkpoints visuals
        for cp in self.checkpoints:
            draw_x = cp['rect'].x - camera_with_shake
            draw_y = cp['rect'].y
            if -32 <= draw_x <= VIRTUAL_WIDTH:
                if cp['activated']:
                    pygame.draw.rect(surf, (80,200,80), (draw_x, draw_y, cp['rect'].width, cp['rect'].height))
                else:
                    pygame.draw.rect(surf, (160,160,160), (draw_x, draw_y, cp['rect'].width, cp['rect'].height))

        # guide popup
        if self.guide_present and not self.guide_betrayed:
            guide_x, guide_y = self.guide_pos
            draw_x = guide_x - camera_with_shake
            draw_y = guide_y + shake_y
            if -32 <= draw_x <= VIRTUAL_WIDTH + 32:
                pygame.draw.circle(surf, (180,220,255), (int(draw_x), int(draw_y)), 10)
                font = pygame.font.SysFont('consolas', 12)
                lbl = font.render('Guide', True, (240,240,240))
                surf.blit(lbl, (draw_x - lbl.get_width()//2, draw_y - 24))

        # enemies
        for e in self.enemies:
            camera_adjusted_rect = e.rect.copy()
            camera_adjusted_rect.x -= camera_with_shake
            if -camera_adjusted_rect.width <= camera_adjusted_rect.x <= VIRTUAL_WIDTH:
                e.draw(surf, camera_with_shake, shake_y)

        # draw items on ground
        for it in self.items_on_ground:
            r = it['rect'].copy()
            r.x -= camera_with_shake
            pygame.draw.rect(surf, (200,200,100), r)
            surf.blit(FONT.render(it['item']['name'], True, (240,240,240)), (r.x, r.y - 10))

        # boss
        if self.boss:
            boss_rect = self.boss.rect.copy()
            boss_rect.x -= camera_with_shake
            if -boss_rect.width <= boss_rect.x <= VIRTUAL_WIDTH:
                self.boss.draw(surf, camera_with_shake, shake_y)

        # player
        self.player.draw(surf, camera_x=camera_with_shake, shake_y=shake_y)

        # damage numbers
        font = pygame.font.SysFont('consolas', 14, bold=True)
        for dmg in self.damage_numbers:
            alpha = int(255 * dmg['life'])
            text = font.render(str(dmg['amount']), True, dmg['color'])
            text.set_alpha(alpha)
            surf.blit(text, (int(dmg['x'] - camera_with_shake), int(dmg['y'] + shake_y)))

        # HUD
        draw_hud(surf, self.player, self.stage_index+1, self.guide_text, lives=self.lives)

        # fade overlay
        if self.fade_state:
            now = time.time()
            t = min(1.0, (now - self.fade_start) / max(0.0001, self.fade_duration))
            if self.fade_state == 'out':
                alpha = int(255 * t)
            else:
                alpha = int(255 * (1.0 - t))
            fade_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha)
            surf.blit(fade_surf, (0, 0))
            if self.fade_state == 'in' and t >= 1.0:
                self.fade_state = None

    def advance_stage_or_end(self):
        if self.stage_index < len(LEVELS) - 1:
            self.stage_index += 1
            self.load_stage(self.stage_index, self.player.char_class)
        else:
            # final endings: use choice_points + guide_help_count to decide
            cp = max(0, self.player.choice_points + self.guide_help_count)
            if cp >= 5:
                self.ending = "Good Ending - Shared Water (Guide saved you)"
            elif cp >= 2:
                self.ending = "Neutral Ending - You drink alone"
            else:
                self.ending = "Bad Ending - Guide betrays you and claims 41 Water"
            return True
        return False

    def start_betrayal_cutscene(self, duration=1.4):
        if self.cutscene_active or self.guide_betrayed:
            return
        now = time.time()
        self.cutscene_active = True
        self.cutscene_end_time = now + duration
        self.guide_text = "Guide: You have done well... drink and be relieved..."
        # after cutscene guide offers choice (B/F) in update()

    def trigger_hitstop(self, duration=0.1):
        self.hitstop_until = time.time() + duration

    def add_screen_shake(self, intensity=3):
        self.screen_shake = max(self.screen_shake, intensity)

    def spawn_damage_number(self, x, y, amount, color=(255, 200, 100)):
        self.damage_numbers.append({
            'x': x,
            'y': y,
            'amount': int(amount),
            'color': color,
            'life': 1.0,
            'created': time.time(),
            'vy': -2
        })

# -------------------------
# Main loop & entry
# -------------------------
def class_select(screen, virtual):
    font = pygame.font.SysFont("consolas", 20)
    options = ["Wizard", "Worrier", "Warrior"]
    sel = 0
    clock = pygame.time.Clock()
    descriptions = {
        "Wizard": "High Magic. Strong spells. Lower HP.",
        "Worrier": "AoE Worrier. Balanced tanking.",
        "Warrior": "High Strength. Heavy melee."
    }
    while True:
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_LEFT:
                    sel = (sel - 1) % len(options)
                if e.key == K_RIGHT:
                    sel = (sel + 1) % len(options)
                if e.key == K_RETURN:
                    return options[sel]
        virtual.fill((12,12,20))
        title = font.render("Choose your class", True, (230,230,230))
        virtual.blit(title, (10,10))
        desc_text = font.render(descriptions.get(options[sel], ""), True, (160,200,160))
        virtual.blit(desc_text, (10, 60))
        for i, opt in enumerate(options):
            col = (255,255,120) if i==sel else (180,180,180)
            virtual.blit(font.render(opt, True, col), (20 + i*120, 120))
        scaled = pygame.transform.scale(virtual, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0,0))
        pygame.display.flip()
        clock.tick(15)

def show_ending(screen, virtual, text):
    font = pygame.font.SysFont("consolas", 28)
    clock = pygame.time.Clock()
    t0 = time.time()
    while time.time() - t0 < 5:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        virtual.fill((8,8,14))
        virtual.blit(font.render("Ending:", True, (220,220,220)), (10,10))
        virtual.blit(font.render(text, True, (220,220,220)), (10,50))
        screen.blit(pygame.transform.scale(virtual, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))
        pygame.display.flip()
        clock.tick(30)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-readme', action='store_true', help='Write README.md then exit')
    args = parser.parse_args()
    if args.write_readme:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(README_TEXT)
        print("README.md written.")
        return

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    virtual = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    gsm = GameStateManager(virtual)

    # class select
    char_class = class_select(screen, virtual)
    gsm.start_new(char_class)

    running = True
    last_attack_pressed = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        inputs = {
            "left": keys[K_LEFT] or keys[K_a],
            "right": keys[K_RIGHT] or keys[K_d],
            "jump": (keys[K_UP] or keys[K_w] or keys[K_SPACE]),
            "dash": keys[K_k],
            "attack": keys[K_j],
        }

        for e in events:
            if e.type == QUIT:
                running = False
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False

        # update world with inputs and events
        gsm.update(dt, inputs, events)

        # action attack (platformer)
        if inputs["attack"] and not last_attack_pressed:
            did = gsm.player.attack()
            if did:
                # compute damage from STR / class
                hb = gsm.player.get_attack_hitbox()
                if hb:
                    damage_base = int(gsm.player.strength * 1.2)
                    if gsm.player.char_class == "Wizard":
                        damage_base = int(gsm.player.magic * 1.5)
                    any_hit = False
                    for e in list(gsm.enemies):
                        if hb.colliderect(e.get_hitbox()):
                            # damage reduced by enemy def roughly
                            dmg = max(1, damage_base + random.randint(-2, 4))
                            e.take_damage(dmg)
                            gsm.spawn_damage_number(e.rect.centerx, e.rect.top, dmg, (255,200,100))
                            any_hit = True
                            # small chance to drop item on kill handled in update
                    # if hit nothing, minimal feedback
                    if not any_hit:
                        gsm.spawn_damage_number(gsm.player.rect.centerx, gsm.player.rect.top, 0, (200,200,200))
            # use choice points slightly when attacking all enemies? (keeps original breadcrumbs)
        last_attack_pressed = inputs["attack"]

        gsm.draw(virtual)
        scaled = pygame.transform.scale(virtual, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0,0))
        pygame.display.flip()

        if gsm.ending:
            show_ending(screen, virtual, gsm.ending)
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
