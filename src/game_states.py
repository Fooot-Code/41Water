# game_states.py
import pygame
import time
import math
from ui import draw_hud
from level import build_level_from_array, LEVELS, TILE_SIZE
from player import Player
from enemy import Enemy
from boss import Boss
from settings import LEVEL_WIDTH, LEVEL_HEIGHT, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
import random

class GameStateManager:
    def __init__(self, screen):
        self.screen = screen
        self.stage_index = 0
        self.player = None
        self.enemies = []
        self.boss = None
        self.tiles = []
        self.tile_surfaces = []
        self.guide_alive = True
        self.guide_text = "Welcome, traveler. Let's find 41 Water."
        self.guide_help_count = 0
        self.ending = None
        # Camera settings
        self.camera_x = 0
        self.camera_y = 0
        self.level_width = LEVEL_WIDTH
        self.level_height = LEVEL_HEIGHT
        # Lives and respawn
        self.lives = 3
        self.respawn_delay = 2.0
        self.respawn_time = None
        self.spawn_point = (32, 32)
        # Checkpoints
        self.checkpoints = []  # list of {'rect':Rect,'activated':bool}

        # Fade / death animation
        self.fade_state = None  # None, 'out', 'in'
        self.fade_start = 0
        self.fade_duration = 1.0

    def start_new(self, char_class):
        # build first stage
        self.stage_index = 0
        self.load_stage(self.stage_index, char_class)

    def load_stage(self, idx, char_class):
        arr = LEVELS[idx]
        tiles, tile_surfaces = build_level_from_array(arr)
        self.tiles = tiles
        self.tile_surfaces = tile_surfaces
        # find player spawn (P)
        spawn = None
        for y, row in enumerate(arr):
            for x, ch in enumerate(row):
                if ch == "P":
                    spawn = (x * TILE_SIZE, y * TILE_SIZE)
        if spawn is None:
            spawn = (32, 32)
        if self.player is None:
            self.player = Player(spawn[0], spawn[1], char_class)
            # give player initial lives
            self.player.lives = self.lives
        else:
            # move player to spawn between stages
            self.player.rect.topleft = spawn
            self.player.vx = self.player.vy = 0
        # store spawn point for respawn
        self.spawn_point = spawn
        # Reposition camera to center on spawn (but clamped)
        self.camera_x = max(0, min(spawn[0] - VIRTUAL_WIDTH // 2, self.level_width - VIRTUAL_WIDTH))

        # Create two automatic checkpoints across the level (1/3 and 2/3)
        self.checkpoints = []
        checkpoint_xs = [int(self.level_width * 0.33), int(self.level_width * 0.66)]
        for cx in checkpoint_xs:
            # find a ground tile at this x
            spawn_y = None
            for t in self.tiles:
                if t.left <= cx <= t.right:
                    if spawn_y is None or t.top < spawn_y:
                        spawn_y = t.top
            if spawn_y is None:
                spawn_y = VIRTUAL_HEIGHT - TILE_SIZE * 2
            cp_rect = pygame.Rect(cx - 8, spawn_y - TILE_SIZE, 16, TILE_SIZE)
            self.checkpoints.append({'rect': cp_rect, 'activated': False})

        # Initialize enemy spawning system
        self.enemies = []
        self.enemy_types = {
            0: ["grub", "grub", "spider"],  # Stage 1: Mostly grubs, one spider
            1: ["grub", "spider", "slime"],  # Stage 2: Mixed types
            2: ["spider", "slime", "ghost"]  # Stage 3: Harder enemies
        }
        self.max_enemies = 6 + idx*2
        self.min_spawn_distance = 200  # Minimum distance from player for spawning
        self.last_spawn_time = time.time()
        self.spawn_cooldown = 3.0  # Time between spawn attempts
        
        # Add initial enemies
        self.spawn_initial_enemies()

        # stage-specific guide text
        self.guide_text = [
            "This land holds 41 Water. Keep your wits.",
            "These caverns test your courage. Stay sharp.",
            "The temple holds what you seek... but not all is as it seems."
        ][idx]

        # final stage sets boss
        if idx == 2:
            self.boss = Boss(600, 100)
        else:
            self.boss = None

    def update(self, dt, inputs):
        # inputs is dict of keys
        now = time.time()

        # Handle player death / respawn
        if getattr(self.player, 'health', 999) <= 0:
            # start respawn if not already scheduled
            if self.respawn_time is None:
                # decrement lives and schedule respawn or game over
                self.lives -= 1
                self.respawn_time = now + self.respawn_delay
                # start fade-out animation leading to respawn
                self.fade_state = 'out'
                self.fade_start = now
                self.fade_duration = self.respawn_delay
                self.player.dead = True
                # clear movement
                self.player.vx = self.player.vy = 0
                # optional: move player off-screen while dead
                self.player.rect.topleft = (-1000, -1000)
                if self.lives < 0:
                    # game over
                    self.ending = "Game Over"
                    return
            else:
                # wait until respawn_time
                if now < self.respawn_time:
                    # still waiting, do not process inputs
                    return
                # respawn now
                self.respawn_time = None
                self.player.dead = False
                self.player.health = self.player.max_health
                self.player.rect.topleft = self.spawn_point
                # brief invulnerability after respawn
                self.player.spawn_time = now
                self.player.invulnerable = True
                # start fade-in
                self.fade_state = 'in'
                self.fade_start = now
                self.fade_duration = 0.8

        # basic player controls
        if inputs.get("left"): self.player.move(-1)
        elif inputs.get("right"): self.player.move(1)
        else: self.player.move(0)

        # Jump with coyote-time handled by Player.update; pass jump input through
        if inputs.get("jump"):
            # Player.jump() will check coyote time internally
            self.player.jump()

        if inputs.get("dash"):
            self.player.start_dash()

        # Update player physics
        self.player.update(dt, self.tiles)

        # Check for checkpoint activation
        for cp in self.checkpoints:
            if not cp['activated'] and self.player.rect.colliderect(cp['rect']):
                cp['activated'] = True
                cp['activation_time'] = time.time()
                # set new spawn point slightly above the checkpoint
                self.spawn_point = (cp['rect'].x, cp['rect'].y - TILE_SIZE)
                self.guide_text = "Checkpoint reached. Your progress is saved."
                # Story progression at checkpoints
                checkpoint_stories = [
                    "These caverns hold secrets of the 41 Water... and those who sought it before.",
                    "Ancient markings suggest a guardian protects the water. Trust may be key.",
                    "The air grows thick with magic. The guide watches your choices carefully."
                ]
                if len(checkpoint_stories) > sum(cp['activated'] for cp in self.checkpoints):
                    self.guide_text = checkpoint_stories[sum(cp['activated'] for cp in self.checkpoints) - 1]

        # Update camera after player moved so spawn area is correct
        self.update_camera()

        # Attempt to spawn off-screen enemies periodically
        self.try_spawn_enemy()

        # Determine whether player currently has spawn/invul protection
        has_protection = (now - getattr(self.player, 'spawn_time', 0)) < getattr(self.player, 'spawn_protection', 0)

        # Update enemies and handle their attacks
        for e in list(self.enemies):
            attacked = e.update(self.tiles, self.player.rect)
            if attacked:
                attack_rect = e.get_attack_rect()
                if attack_rect and attack_rect.colliderect(self.player.rect) and not has_protection:
                    # Apply damage and give brief invulnerability window
                    self.player.health -= e.damage
                    self.player.spawn_time = now  # reuse spawn_time as temporary invul timer

        # Remove dead enemies
        self.enemies = [e for e in self.enemies if not getattr(e, "dead", False)]

        # Stage progression: check during movement and dash
        edge_threshold = self.level_width - 60
        if (self.player.rect.right >= edge_threshold or 
            (self.player.dashing and 
             self.player.rect.right + (self.player.dash_speed * self.player.facing) >= edge_threshold)):
            if len(self.enemies) == 0 and not self.boss:
                # Progressive story elements before advancing
                stage_completion_text = [
                    "The path opens ahead. The guide nods approvingly at your progress.",
                    "Ancient mechanisms whir to life, revealing the next chamber.",
                    "The final gate awaits. The guide's expression is unreadable."
                ]
                if self.stage_index < len(stage_completion_text):
                    self.guide_text = stage_completion_text[self.stage_index]
                
                advanced = self.advance_stage_or_end()
                if advanced:
                    # loaded next stage; early return so we don't update boss on old stage
                    return
            else:
                self.guide_text = "Clear the area of enemies before proceeding."

        # Boss update
        if self.boss:
            self.boss.update(self.tiles, self.player.rect)

        # guide helps occasionally (increases guide_help_count)
        if len(self.enemies) < 2 and self.guide_help_count < 3:
            self.guide_help_count += 1

    def player_attack_check(self):
        # check attack hit detection (melee)
        rect = self.player.rect
        if self.player.attack():
            # make hitbox in front of player
            hb_w = self.player.attack_range * 2
            hb_h = rect.height - 4
            if self.player.facing > 0:
                hitbox = pygame.Rect(rect.right, rect.top+2, hb_w, hb_h)
            else:
                hitbox = pygame.Rect(rect.left - hb_w, rect.top+2, hb_w, hb_h)
            damage = 30 if self.player.char_class == "Worrier" else 20
            # damage enemies
            for e in self.enemies:
                if hitbox.colliderect(e.rect):
                    e.take_damage(damage)
            # if boss present
            if self.boss and hitbox.colliderect(self.boss.rect):
                self.boss.take_damage(damage)
            return True
        return False

    def dash_collision_check(self):
        # if dashing, touching enemies damages them, and player is invulnerable briefly
        if self.player.dashing:
            for e in self.enemies:
                if self.player.rect.colliderect(e.rect):
                    e.take_damage(40)
            if self.boss and self.player.rect.colliderect(self.boss.rect):
                self.boss.take_damage(15)

    def spawn_initial_enemies(self):
        """Spawn initial enemies away from the player's starting position"""
        for i in range(3):  # Start with fewer enemies
            valid_spawn = False
            attempts = 0
            while not valid_spawn and attempts < 10:
                ex = random.randint(int(VIRTUAL_WIDTH * 0.7), int(LEVEL_WIDTH * 0.8))
                ey = random.randint(40, int(VIRTUAL_HEIGHT * 0.7))
                # Check if spawn point is valid (not inside tiles)
                valid_spawn = True
                spawn_rect = pygame.Rect(ex, ey, 32, 32)
                for tile in self.tiles:
                    if spawn_rect.colliderect(tile):
                        valid_spawn = False
                        break
                attempts += 1
            
            if valid_spawn:
                enemy_kind = random.choice(self.enemy_types[self.stage_index])
                self.enemies.append(Enemy(ex, ey, kind=enemy_kind))

    def try_spawn_enemy(self):
        """Attempt to spawn a new enemy if conditions are met"""
        now = time.time()
        if (now - self.last_spawn_time < self.spawn_cooldown or 
            len(self.enemies) >= self.max_enemies):
            return

        # Calculate valid spawn area just off the right side of the camera
        # so enemies appear to come into view
        spawn_left = int(self.camera_x + VIRTUAL_WIDTH + 16)
        spawn_right = int(min(spawn_left + (VIRTUAL_WIDTH // 2), LEVEL_WIDTH - 100))

        # If there's no room to spawn (camera near level end), skip spawning
        if spawn_left >= spawn_right:
            return

        valid_spawn = False
        attempts = 0
        while not valid_spawn and attempts < 10:
            ex = random.randint(spawn_left, spawn_right)
            ey = random.randint(40, int(VIRTUAL_HEIGHT * 0.7))
            
            # Check distance from player
            dx = ex - self.player.rect.centerx
            dy = ey - self.player.rect.centery
            dist = (dx*dx + dy*dy) ** 0.5
            
            if dist < self.min_spawn_distance:
                attempts += 1
                continue

            # Check if spawn point is valid (not inside tiles)
            valid_spawn = True
            spawn_rect = pygame.Rect(ex, ey, 32, 32)
            for tile in self.tiles:
                if spawn_rect.colliderect(tile):
                    valid_spawn = False
                    break
            attempts += 1

        if valid_spawn:
            enemy_kind = random.choice(self.enemy_types[self.stage_index])
            self.enemies.append(Enemy(ex, ey, kind=enemy_kind))
            self.last_spawn_time = now

    def update_camera(self):
        # Update camera position to follow player
        target_x = self.player.rect.centerx - VIRTUAL_WIDTH // 2
        
        # Smooth camera movement
        self.camera_x += (target_x - self.camera_x) * 0.1
        
        # Clamp camera to level boundaries and prevent going left
        self.camera_x = max(0, min(self.camera_x, self.level_width - VIRTUAL_WIDTH))
        
        # Prevent player from going too far left
        if self.player.rect.left < self.camera_x + 20:
            self.player.rect.left = self.camera_x + 20
            self.player.vx = max(0, self.player.vx)  # Stop leftward movement
    
    def draw(self, surf):
        # background
        surf.fill((50, 60, 80))
        
        # Update camera position
        self.update_camera()
        
        # tiles (with camera offset)
        for tile_surf, pos in self.tile_surfaces:
            camera_adjusted_pos = (pos[0] - self.camera_x, pos[1])
            # Only draw if on screen
            if -tile_surf.get_width() <= camera_adjusted_pos[0] <= VIRTUAL_WIDTH:
                surf.blit(tile_surf, camera_adjusted_pos)
            # Draw checkpoints with enhanced visuals
            for cp in self.checkpoints:
                draw_x = cp['rect'].x - self.camera_x
                draw_y = cp['rect'].y
                if -32 <= draw_x <= VIRTUAL_WIDTH:
                    now = time.time()
                    activation_time = cp.get('activation_time', now)
                    
                    if cp['activated']:
                        # Fade from gray to green over 1 second
                        progress = min(1.0, (now - activation_time))
                        green = int(180 + (75 * progress))  # 180 -> 255
                        gray = int(180 - (80 * progress))   # 180 -> 100
                        color = (gray, green, gray)
                        
                        # Expanding activation ring
                        ring_size = int(20 * progress)
                        if progress < 1.0:
                            ring_rect = (
                                draw_x - ring_size//2,
                                draw_y - ring_size//2,
                                cp['rect'].width + ring_size,
                                cp['rect'].height + ring_size
                            )
                            pygame.draw.rect(surf, (100, 255, 100), ring_rect, 2)
                        
                        # Pulsing glow effect
                        pulse = (math.sin(now * 4) + 1) / 2
                        glow_alpha = int(60 + 40 * pulse)
                        glow_surf = pygame.Surface((cp['rect'].width + 8, cp['rect'].height + 8))
                        glow_surf.fill((100, 255, 100))
                        glow_surf.set_alpha(glow_alpha)
                        surf.blit(glow_surf, (draw_x - 4, draw_y - 4))
                        
                        # Draw checkpoint symbol
                        symbol_x = draw_x + cp['rect'].width // 2
                        symbol_y = draw_y + cp['rect'].height // 2
                        symbol_color = (50, 200, 50)
                        points = [
                            (symbol_x - 4, symbol_y),
                            (symbol_x, symbol_y + 4),
                            (symbol_x + 8, symbol_y - 8)
                        ]
                        pygame.draw.lines(surf, symbol_color, False, points, 2)
                    else:
                        # Inactive checkpoint
                        color = (180, 180, 180)
                        # Subtle hover effect when player is near
                        if self.player:
                            dist_to_player = abs(self.player.rect.centerx - (cp['rect'].x + cp['rect'].width//2))
                            if dist_to_player < 100:
                                hover = (100 - dist_to_player) / 100
                                color = (180, min(255, 180 + int(75 * hover)), 180)
                    
                    # Draw main checkpoint rectangle
                    pygame.draw.rect(surf, color, (draw_x, draw_y, cp['rect'].width, cp['rect'].height))        # enemies (with camera offset)
        for e in self.enemies:
            camera_adjusted_rect = e.rect.copy()
            camera_adjusted_rect.x -= self.camera_x
            # Only draw if on screen
            if -camera_adjusted_rect.width <= camera_adjusted_rect.x <= VIRTUAL_WIDTH:
                e.draw(surf, self.camera_x)
        
        # boss (with camera offset)
        if self.boss:
            boss_rect = self.boss.rect.copy()
            boss_rect.x -= self.camera_x
            if -boss_rect.width <= boss_rect.x <= VIRTUAL_WIDTH:
                self.boss.draw(surf, self.camera_x)
        
        # player (with camera offset)
        player_rect = self.player.rect.copy()
        player_rect.x -= self.camera_x
        self.player.draw(surf, self.camera_x)
        
        # HUD and guide text (no camera offset - stays fixed on screen)
        draw_hud(surf, self.player, self.stage_index+1, self.guide_text, lives=self.lives)

        # Fade overlay for death/respawn
        if self.fade_state:
            now = time.time()
            t = min(1.0, (now - self.fade_start) / max(0.0001, self.fade_duration))
            if self.fade_state == 'out':
                alpha = int(255 * t)
            else:  # 'in'
                alpha = int(255 * (1.0 - t))
            fade_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(alpha)
            surf.blit(fade_surf, (0, 0))
            # finish fade-in state
            if self.fade_state == 'in' and t >= 1.0:
                self.fade_state = None

    def advance_stage_or_end(self):
        # call to advance to next stage, or finish
        if self.stage_index < 2:
            self.stage_index += 1
            self.load_stage(self.stage_index, self.player.char_class)
        else:
            # reached the "41 Water" location — decide ending
            # decision logic:
            # - if you attacked the guide (tracked by choice_points) or ignored guidance, bad ending
            # - if you saved/obeyed the guide, good ending
            # - if you drank it selfishly (e.g., killed many enemies?), neutral
            cp = self.player.choice_points + self.guide_help_count
            if cp >= 5:
                self.ending = "Good Ending — Shared Water (Guide saved you)"
            elif cp >= 2:
                self.ending = "Neutral Ending — You drink alone"
            else:
                self.ending = "Bad Ending — Guide betrays you and claims 41 Water"
            return True
        return False

    def guide_turns_boss(self):
        # Called in final boss sequence: guide reveals themselves and becomes the boss
        # The presence of boss variable simulates that
        pass
