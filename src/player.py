# player.py
import pygame
import random
import math
from settings import (PLAYER_SPEED, PLAYER_JUMP_SPEED, GRAVITY, TERMINAL_VEL, 
                     PLAYER_WIDTH, PLAYER_HEIGHT, VIRTUAL_WIDTH)
from assets import generate_player_sprite
import time

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, char_class="Wizard"):
        super().__init__()
        self.char_class = char_class
        self.idle_surf, self.attack_surf, self.dash_surf = generate_player_sprite(char_class)
        self.image = self.idle_surf
        self.current_sprite = self.idle_surf  # For animation handling
        self.rect = self.image.get_rect(topleft=(x,y))
        # physics
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.was_on_ground = False  # For better ground detection
        self.coyote_time = 0.1  # Time window to jump after leaving platform
        self.last_ground_time = 0
        # combat
        self.attacking = False
        self.attack_frame = 0
        self.spawn_protection = 2.0  # 2 seconds of spawn protection
        self.spawn_time = time.time()
        # particles
        self.particles = []
        self.dash_particles = []
        # state
        self.dead = False
        # combat
        self.facing = 1
        self.health = 100
        self.max_health = 100
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
        # stats based on class
        if char_class == "Wizard":
            self.max_health = 80
            self.health = 80
            self.attack_cooldown = 0.35
            self.magic_power = 50
            self.defense = 15
            self.speed = 2.0
            self.special_ability = "Magic Shield"
        elif char_class == "Worrier":
            self.max_health = 120
            self.health = 120
            self.attack_cooldown = 0.5
            self.magic_power = 10
            self.defense = 40
            self.speed = 1.8
            self.special_ability = "Worry Sphere"
        
        # choices (for endings)
        self.choice_points = 0

    def get_hitbox(self):
        # Slightly smaller hitbox than visual sprite for better feel
        return pygame.Rect(
            self.rect.left + 4,
            self.rect.top + 2,
            self.rect.width - 8,
            self.rect.height - 4
        )

    def move(self, dx):
        self.vx = dx * PLAYER_SPEED
        if dx != 0:
            self.facing = 1 if dx > 0 else -1

    def jump(self):
        now = time.time()
        # Allow jump from ground or within coyote time window after leaving ground
        if self.on_ground or (now - getattr(self, 'last_ground_time', 0) <= getattr(self, 'coyote_time', 0)):
            self.vy = PLAYER_JUMP_SPEED
            self.on_ground = False

    def start_dash(self):
        now = time.time()
        # Calculate cooldown progress (0 to 1)
        cooldown_progress = min(1.0, (now - getattr(self, 'last_dash_time', 0)) / 1.0)
        
        if not self.dashing and self.can_dash and cooldown_progress >= 1.0:
            self.dashing = True
            self.invulnerable = True
            self.dash_start = now
            self.last_dash_time = now
            self.can_dash = False
            
            # Class-specific dash properties
            if self.char_class == "Wizard":
                self.dash_time = 0.15  # Shorter teleport-like dash
                self.dash_speed = 10
            elif self.char_class == "Worrier":
                self.dash_time = 0.25  # Longer charging dash
                self.dash_speed = 7
            elif self.char_class == "Ranger":
                self.dash_time = 0.18  # Quick agile dash
                self.dash_speed = 9

    def attack(self):
        now = time.time()
        if now - self.last_attack >= self.attack_cooldown:
            self.last_attack = now
            self.attacking = True
            self.attack_frame = 12
            
            # Class-specific attack properties
            if self.char_class == "Wizard":
                # Magic bolt - ranged magical attack
                self.attack_range = 45
                self.attack_height = 16
                self.attack_frame = 15
            elif self.char_class == "Worrier":
                # Worry Sphere - AOE around player
                self.attack_range = 40
                self.attack_height = 80
                self.attack_frame = 12
            return True
        return False
        
    def get_attack_hitbox(self):
        """Get the current attack's hitbox if attacking"""
        if not self.attacking or self.attack_frame <= 0:
            return None
            
        progress = self.attack_frame / 12.0
        
        if self.char_class == "Worrier":
            # Worry Sphere - circular AOE expanding from center
            sphere_radius = int(self.attack_range * progress)
            return pygame.Rect(
                self.rect.centerx - sphere_radius,
                self.rect.centery - sphere_radius,
                sphere_radius * 2,
                sphere_radius * 2
            )
        
        else:  # Wizard
            # Magic bolt - rectangular projectile
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
        self.on_ground = False  # Will be set true in collision check if needed

        # Apply gravity with better fall detection
        if not self.on_ground:
            self.vy += GRAVITY
            if self.vy > TERMINAL_VEL:
                self.vy = TERMINAL_VEL
            
        # Animation handling
        if now - self.last_attack < 0.2:  # Attack animation duration
            self.image = self.attack_surf
        elif self.dashing:
            self.image = self.dash_surf
        else:
            self.image = self.idle_surf
        
        # Flip sprite based on facing direction
        if self.facing < 0:
            self.image = pygame.transform.flip(self.image, True, False)
            
        # Dash logic and particles
        if self.dashing:
            self.vx = self.facing * self.dash_speed
            if now - self.dash_start >= self.dash_time:
                self.dashing = False
                self.invulnerable = False
                self.can_dash = True  # Reset dash ability when landing
            
            # Create dash particles
            for _ in range(2):  # Number of particles per frame
                particle = {
                    'x': self.rect.centerx + random.randint(-5, 5),
                    'y': self.rect.centery + random.randint(-10, 10),
                    'life': 0.5,
                    'color': (200, 200, 255),
                    'size': random.randint(2, 4),
                    'created': now
                }
                self.dash_particles.append(particle)
        
        # Update particles
        self.dash_particles = [p for p in self.dash_particles if now - p['created'] < p['life']]
        
        # Movement integration with subpixel precision
        self.rect.x += int(self.vx)
        self.resolve_collisions('x', tiles)
        self.rect.y += int(self.vy)
        self.resolve_collisions('y', tiles)
        
        # Update coyote time after collisions so we detect leaving ground correctly
        if self.was_on_ground and not self.on_ground:
            self.last_ground_time = now

        # Enable dash after touching ground
        if self.on_ground:
            self.can_dash = True

        # Attack animation frame update
        if self.attacking:
            if self.attack_frame > 0:
                self.attack_frame -= 1
            else:
                self.attacking = False

        # Reset horizontal velocity if not dashing
        if not self.dashing:
            self.vx = 0

    def resolve_collisions(self, axis, tiles):
        # tiles: list of rects
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

    def draw(self, surface, camera_x=0):
        now = time.time()
        
        # Draw dash particles with trails
        for particle in self.dash_particles:
            particle_x = particle['x'] - camera_x
            if -particle['size'] <= particle_x <= VIRTUAL_WIDTH:
                life_progress = (now - particle['created']) / particle['life']
                # Fade out
                alpha = int(255 * (1 - life_progress))
                # Trail effect - draw multiple fading copies
                for i in range(3):
                    trail_x = particle_x - (i * 2 * self.facing)
                    trail_alpha = alpha // (i + 1)
                    trail_surf = pygame.Surface((particle['size'], particle['size']))
                    trail_surf.fill(particle['color'])
                    trail_surf.set_alpha(trail_alpha)
                    surface.blit(trail_surf, (trail_x, particle['y']))
        
        # Draw the player with special effects
        draw_pos = (self.rect.x - camera_x, self.rect.y)
        base_image = self.image.copy()
        
        # Add class-specific idle effects
        if not self.attacking and not self.dashing:
            if self.char_class == "Wizard":
                # Magical sparkle effect
                if random.random() < 0.1:
                    sparkle_x = draw_pos[0] + random.randint(-5, self.rect.width + 5)
                    sparkle_y = draw_pos[1] + random.randint(-5, self.rect.height + 5)
                    sparkle_size = random.randint(1, 3)
                    sparkle_surf = pygame.Surface((sparkle_size, sparkle_size))
                    sparkle_surf.fill((200, 200, 255))
                    sparkle_surf.set_alpha(random.randint(100, 200))
                    surface.blit(sparkle_surf, (sparkle_x, sparkle_y))
            elif self.char_class == "Worrier":
                # Battle aura when health is low
                if self.health < self.max_health * 0.3:
                    aura_pulse = (math.sin(now * 8) + 1) / 2
                    aura_surf = base_image.copy()
                    aura_surf.fill((200, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    aura_surf.set_alpha(int(100 * aura_pulse))
                    surface.blit(aura_surf, draw_pos)
            elif self.char_class == "Ranger":
                # Speed trail when moving
                if abs(self.vx) > 0:
                    trail_surf = base_image.copy()
                    trail_surf.set_alpha(80)
                    trail_x = draw_pos[0] - (self.facing * 4)
                    surface.blit(trail_surf, (trail_x, draw_pos[1]))
        
        # Draw the base player sprite
        surface.blit(base_image, draw_pos)
        
        # Enhanced attack effect
        if self.attacking and self.attack_frame > 0:
            progress = self.attack_frame / 12.0
            
            if self.char_class == "Worrier":
                # Draw worry sphere - ONLY (no arrow)
                sphere_radius = int(self.attack_range * progress)
                center_x = draw_pos[0] + self.rect.width//2
                center_y = self.rect.centery
                
                # Draw multiple expanding rings
                for i in range(3):
                    ring_progress = progress * (1 - i * 0.2)
                    if ring_progress <= 0: continue
                    
                    ring_radius = int(sphere_radius * (1 - i * 0.2))
                    ring_alpha = int(200 * ring_progress)
                    
                    # Create surface for the ring
                    ring_size = ring_radius * 2 + 4
                    ring_surf = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
                    
                    # Draw expanding ring
                    pygame.draw.circle(ring_surf, (255, 180, 180, ring_alpha), 
                                    (ring_radius + 2, ring_radius + 2), ring_radius, 3)
                    
                    # Add energy particles
                    for _ in range(5):
                        particle_angle = random.uniform(0, math.pi * 2)
                        particle_dist = random.uniform(0.5, 0.9) * ring_radius
                        particle_x = ring_radius + 2 + math.cos(particle_angle) * particle_dist
                        particle_y = ring_radius + 2 + math.sin(particle_angle) * particle_dist
                        particle_size = random.randint(2, 4)
                        pygame.draw.circle(ring_surf, (255, 80, 80, ring_alpha),
                                        (int(particle_x), int(particle_y)), particle_size)
                    
                    # Draw aura waves
                    wave_points = []
                    num_points = 20
                    for j in range(num_points):
                        angle = j * (2 * math.pi / num_points)
                        wave = math.sin(angle * 4 + now * 10) * 5
                        x = ring_radius + 2 + math.cos(angle) * (ring_radius + wave)
                        y = ring_radius + 2 + math.sin(angle) * (ring_radius + wave)
                        wave_points.append((x, y))
                    
                    if len(wave_points) > 2:
                        pygame.draw.lines(ring_surf, (255, 120, 120, ring_alpha), True, wave_points, 2)
                    
                    # Blit the ring
                    surface.blit(ring_surf, (center_x - ring_radius - 2, center_y - ring_radius - 2))
                
            else:  # Wizard
                # Main attack swish
                attack_width = int(self.attack_range * progress)
                attack_height = 20 + int(10 * (1 - progress))  # Varies height for more dynamic feel
                
                if self.facing > 0:
                    attack_x = (self.rect.right - camera_x)
                else:
                    attack_x = (self.rect.left - attack_width - camera_x)
                
                # Draw standard magic attack
                for i in range(3):
                    layer_progress = progress * (1 - i * 0.2)
                    if layer_progress <= 0: continue
                    
                    attack_rect = pygame.Rect(
                        attack_x, 
                        self.rect.centery - (attack_height//2) + (i * 2),
                        max(1, attack_width),
                        attack_height - (i * 4)
                    )
                    
                    alpha = int(160 * layer_progress)
                    alpha_surf = pygame.Surface((attack_rect.width, attack_rect.height))
                    alpha_surf.fill((100, 100, 255))
                    alpha_surf.set_alpha(alpha)
                    surface.blit(alpha_surf, attack_rect)
                
                # Add particles at the attack point
                if progress > 0.2:
                    for _ in range(3):
                        particle_x = attack_x + (attack_width * 0.7 * random.random())
                        particle_y = self.rect.centery + random.randint(-15, 15)
                        size = random.randint(2, 4)
                        p_surf = pygame.Surface((size, size))
                        p_surf.fill((100, 100, 255))  # Blue magic
                        p_surf.set_alpha(int(200 * progress))
                        surface.blit(p_surf, (particle_x, particle_y))
                    
        # Draw dash cooldown indicator
        cooldown_progress = min(1.0, (now - getattr(self, 'last_dash_time', 0)) / 1.0)
        if cooldown_progress < 1.0:
            # Draw cooldown arc above player
            indicator_radius = 12
            center_x = draw_pos[0] + self.rect.width // 2
            center_y = draw_pos[1] - indicator_radius - 5
            
            # Background circle
            pygame.draw.circle(surface, (50, 50, 50, 128), (center_x, center_y), indicator_radius)
            
            # Progress arc (from full to empty)
            start_angle = -90  # Start from top
            end_angle = start_angle + (360 * (1 - cooldown_progress))
            if end_angle != start_angle:  # Only draw if there's a visible arc
                pygame.draw.arc(surface, (200, 200, 255), 
                              (center_x - indicator_radius, center_y - indicator_radius,
                               indicator_radius * 2, indicator_radius * 2),
                              math.radians(start_angle), math.radians(end_angle), 3)

    def draw_scaled(self, surf):
        self.draw(surf)
