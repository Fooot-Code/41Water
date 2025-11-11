# enemy.py - Improved enemy system with better AI
import pygame
from assets import generate_enemy_sprite
import random
import time
import math

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, kind="grub"):
        super().__init__()
        self.surf = generate_enemy_sprite(kind)
        self.image = self.surf
        self.rect = self.image.get_rect(topleft=(x,y))
        self.kind = kind
        
        # Physics
        self.vx = random.choice([-1, 1]) * 0.6
        self.vy = 0
        self.on_ground = False
        self.dead = False
        
        # Combat
        self.last_hurt = 0
        self.last_attack = -2.0
        self.attacking = False
        self.attack_frame = 0
        
        # AI System
        self.decision_timer = 0
        self.decision_interval = random.uniform(0.5, 2.0)
        self.aggression = random.uniform(0.4, 0.8)  # How likely to attack
        self.confidence = random.uniform(0.5, 1.0)  # How close to get
        self.hit_particles = []
        
        # Enemy-specific stats and behaviors
        if kind == "grub":
            self.max_health = 35
            self.health = self.max_health
            self.speed = 0.8
            self.damage = 12
            self.attack_range = 45
            self.attack_cooldown = 2.0
            self.behavior = "patrol"
            self.burrow_cooldown = 0
            self.burrowed = False
            self.burrow_time = 0
            
        elif kind == "spider":
            self.max_health = 25
            self.health = self.max_health
            self.speed = 1.4
            self.damage = 15
            self.attack_range = 70
            self.attack_cooldown = 1.8
            self.behavior = "chase"
            self.jump_cooldown = 0
            self.web_cooldown = 0
            self.web_charges = 2
            
        elif kind == "slime":
            self.max_health = 45
            self.health = self.max_health
            self.speed = 0.7
            self.damage = 10
            self.attack_range = 35
            self.attack_cooldown = 2.2
            self.behavior = "bounce"
            self.jump_timer = 0
            self.size = 2
            self.regeneration = 1.0
            
        elif kind == "ghost":
            self.max_health = 30
            self.health = self.max_health
            self.speed = 1.1
            self.damage = 14
            self.attack_range = 55
            self.attack_cooldown = 1.9
            self.behavior = "phase"
            self.phase_timer = 0
            self.visible = True
            self.energy = 100
            self.energy_regen = 8
        
        self.level = 1
        self.exp_value = 10 * self.level
        self.status_effects = []
        self.combo_counter = 0
        self.last_ability_time = time.time()

    def update(self, tiles, player_rect=None):
        now = time.time()
        dt = now - self.last_ability_time
        self.last_ability_time = now
        
        # Update status effects
        self.update_status_effects(dt)
        
        # Update AI decision-making
        self.decision_timer += dt
        if self.decision_timer >= self.decision_interval:
            self.decision_timer = 0
            self.decision_interval = random.uniform(0.5, 2.0)
        
        # Update behavior based on player
        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Adjust attack range based on aggression and health
            health_percent = self.health / self.max_health
            attack_range_modifier = self.aggression * (0.5 + health_percent)
            effective_attack_range = self.attack_range * (0.8 + attack_range_modifier)
            
            # Update behavior
            if self.behavior == "patrol":
                self.update_grub_behavior(dist, dx, dy, dt, now)
            elif self.behavior == "chase":
                self.update_spider_behavior(dist, dx, dy, dt, now)
            elif self.behavior == "bounce":
                self.update_slime_behavior(dist, dx, dy, dt, now)
            elif self.behavior == "phase":
                self.update_ghost_behavior(dist, dx, dy, dt, now)
            
            # Attack logic
            if dist <= effective_attack_range and now - self.last_attack >= self.attack_cooldown:
                # Aggression-based attack chance
                attack_chance = self.aggression + (1 - health_percent) * 0.3
                if random.random() < attack_chance:
                    self.attacking = True
                    self.last_attack = now
                    self.attack_frame = 10
                    return True
        
        # Apply physics
        self.apply_physics(tiles)
        
        # Update attack animation
        if self.attacking:
            self.attack_frame -= 1
            if self.attack_frame <= 0:
                self.attacking = False
        
        # Check death
        if self.health <= 0:
            self.dead = True
        
        return False
    
    def update_grub_behavior(self, dist, dx, dy, dt, now):
        """Grub behavior: Patrol with burrowing"""
        patrol_range = 150
        burrow_distance = 60
        
        if not self.burrowed:
            if dist < burrow_distance and self.burrow_cooldown <= 0 and random.random() < 0.01 * self.aggression:
                # Burrow when threatened
                self.burrowed = True
                self.burrow_time = now
                self.vx = 0
            elif dist < patrol_range:
                # Chase player cautiously
                self.vx = math.copysign(self.speed * (dist / patrol_range), dx)
            else:
                # Idle patrol
                if random.random() < 0.01:
                    self.vx = random.choice([-1, 1]) * self.speed
        else:
            # Burrowed behavior
            if now - self.burrow_time > 2.0:
                self.burrowed = False
                self.burrow_cooldown = 5.0
                if dist < 60:  # Emerge with attack if player nearby
                    self.attacking = True
                    self.attack_frame = 12
        
        if self.burrow_cooldown > 0:
            self.burrow_cooldown -= dt
    
    def update_spider_behavior(self, dist, dx, dy, dt, now):
        """Spider behavior: Chase with jumps and web attacks"""
        chase_range = 200
        optimal_range = 80
        
        if dist < chase_range:
            if dist < optimal_range:
                # Maintain distance, strafe around player
                self.vx = -math.copysign(self.speed * 0.6, dx)
            else:
                # Chase player
                self.vx = math.copysign(self.speed * 1.2, dx)
            
            # Jump frequently
            if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.08 * self.aggression:
                self.vy = -7
                self.jump_cooldown = 1.5
            
            # Occasional web attack
            if self.web_cooldown <= 0 and random.random() < 0.03 * self.aggression:
                self.web_cooldown = 2.0
        
        if self.jump_cooldown > 0:
            self.jump_cooldown -= dt
        if self.web_cooldown > 0:
            self.web_cooldown -= dt
    
    def update_slime_behavior(self, dist, dx, dy, dt, now):
        """Slime behavior: Bouncing and regeneration"""
        self.jump_timer += dt
        
        # Regenerate health
        self.health = min(self.max_health, self.health + self.regeneration * dt * 0.1)
        
        if self.on_ground and self.jump_timer >= 1.5:
            # Jump toward or away from player
            if dist < 200:
                jump_power = -5 - (200 - dist) / 80
                self.vx = math.copysign(self.speed * 1.3, dx)
            else:
                self.vx = random.choice([-1, 1]) * self.speed
                jump_power = -4
            
            self.vy = jump_power
            self.jump_timer = 0
    
    def update_ghost_behavior(self, dist, dx, dy, dt, now):
        """Ghost behavior: Phasing and energy-based attacks"""
        self.phase_timer += dt
        self.energy = min(100, self.energy + self.energy_regen * dt)
        
        # Phase every 3 seconds
        if self.phase_timer >= 3.0:
            self.visible = not self.visible
            self.phase_timer = 0
            
            # Attack when becoming visible if player is close
            if self.visible and dist < 100 and self.energy >= 30 and random.random() < self.aggression:
                self.attacking = True
                self.attack_frame = 12
                self.energy -= 30
        
        # Movement
        if dist < 180:
            speed_mult = 1.2 if not self.visible else 0.8
            self.vx = math.copysign(self.speed * speed_mult, dx)
            if not self.visible:
                self.energy = max(0, self.energy - 5 * dt)
    
    def apply_physics(self, tiles):
        """Apply movement and collision physics"""
        if self.behavior == "phase":
            # Ghosts have special physics
            self.rect.x += int(self.vx)
            self.rect.y += int(self.vy)
            
            # Wrap around screen or gentle collision
            for t in tiles:
                if self.rect.colliderect(t):
                    self.vx *= -1
            return
        
        # Standard physics
        # Horizontal movement
        self.rect.x += int(self.vx)
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vx > 0:
                    self.rect.right = t.left
                else:
                    self.rect.left = t.right
                
                if self.kind == "spider" and random.random() < 0.3:
                    self.vy = -4  # Wall jump
                else:
                    self.vx *= -0.8
        
        # Vertical movement
        if not self.on_ground:
            gravity = 0.5 if self.kind == "slime" else 0.7
            self.vy += gravity
        
        max_fall = 10 if self.kind == "spider" else 12
        self.vy = min(self.vy, max_fall)
        
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
    
    def take_damage(self, damage):
        """Handle taking damage with visual feedback"""
        now = time.time()
        if now - self.last_hurt < 0.15:
            return
        
        self.last_hurt = now
        self.health -= damage
        
        # Create hit particles
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            self.hit_particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 0.5,
                'color': (255, 200, 200)
            })
    
    def draw(self, surf, camera_x, shake_y=0):
        """Draw enemy with effects"""
        draw_pos = (self.rect.x - camera_x, self.rect.y + shake_y)
        now = time.time()
        
        # Get base image
        base_image = self.image.copy()
        
        # Phase effect for ghosts
        if self.behavior == "phase":
            if not self.visible:
                base_image.set_alpha(100)
            else:
                pulse = (math.sin(now * 6) + 1) / 2
                base_image.set_alpha(180 + int(75 * pulse))
        
        # Damage highlight
        if now - self.last_hurt < 0.3:
            flash_alpha = int(255 * (1 - (now - self.last_hurt) / 0.3))
            flash_surf = base_image.copy()
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_alpha)
            surf.blit(flash_surf, draw_pos)
        
        # Draw base sprite
        surf.blit(base_image, draw_pos)
        
        # Draw hit particles
        for particle in list(self.hit_particles):
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.05
            if particle['life'] <= 0:
                self.hit_particles.remove(particle)
            else:
                alpha = int(255 * (particle['life'] / 0.5))
                p_surf = pygame.Surface((3, 3))
                p_surf.fill(particle['color'])
                p_surf.set_alpha(alpha)
                p_pos = (int(particle['x'] - camera_x), int(particle['y'] + shake_y))
                surf.blit(p_surf, p_pos)
        
        # Draw health bar
        health_width = 24
        health_height = 3
        bar_y = draw_pos[1] - 8
        
        # Background
        pygame.draw.rect(surf, (60, 60, 60), 
                        (draw_pos[0] + 4, bar_y, health_width, health_height))
        
        # Health bar
        health_percent = self.health / self.max_health
        health_color = (100, 255, 100) if health_percent > 0.5 else (255, 255, 100) if health_percent > 0.2 else (255, 100, 100)
        pygame.draw.rect(surf, health_color,
                        (draw_pos[0] + 4, bar_y, int(health_width * health_percent), health_height))
        pygame.draw.rect(surf, (0, 0, 0), (draw_pos[0] + 4, bar_y, health_width, health_height), 1)
        
        # Attack telegraph
        if self.attacking and self.attack_frame > 0:
            attack_progress = self.attack_frame / 10.0
            pygame.draw.circle(surf, (255, 100, 100, 100), 
                             (int(draw_pos[0] + 8), int(draw_pos[1] + 8)), 
                             int(20 * attack_progress))
    
    def get_hitbox(self):
        """Get collision hitbox based on enemy type"""
        if self.kind == "spider":
            return pygame.Rect(self.rect.x + 6, self.rect.y + 4, 
                             self.rect.width - 12, self.rect.height - 6)
        elif self.kind == "slime":
            return pygame.Rect(self.rect.x + 2, self.rect.y + self.rect.height//2,
                             self.rect.width - 4, self.rect.height//2)
        else:
            return pygame.Rect(self.rect.x + 4, self.rect.y + 4,
                             self.rect.width - 8, self.rect.height - 8)
    
    def get_attack_rect(self):
        """Get attack hitbox"""
        if not self.attacking or self.attack_frame <= 0:
            return None
        
        progress = self.attack_frame / 10.0
        attack_size = int(30 * progress)
        
        if self.kind == "grub":
            return pygame.Rect(self.rect.centerx - attack_size, self.rect.centery - attack_size,
                             attack_size * 2, attack_size * 2)
        else:
            return pygame.Rect(self.rect.centerx - attack_size//2, self.rect.centery - attack_size//2,
                             attack_size, attack_size)
    
    def update_status_effects(self, dt):
        """Update status effects"""
        for effect in list(self.status_effects):
            effect['duration'] -= dt
            if effect['duration'] <= 0:
                self.status_effects.remove(effect)
