# enemy.py
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
        
        # Enhanced movement variables
        self.vx = random.choice([-1, 1]) * 0.6
        self.vy = 0
        self.on_ground = False
        self.movement_timer = 0
        self.next_movement_change = random.uniform(1.0, 3.0)
        self.movement_state = "patrol"
        
        # Combat variables
        self.dead = False
        self.last_hurt = 0
        self.attack_timer = 0
        self.attack_cooldown = 2.0
        self.last_attack = -2.0  # Start with attack ready
        self.attacking = False
        self.attack_frame = 0
        
        # Enemy-specific movement settings
        if kind == "grub":
            self.base_speed = 0.8
            self.movement_patterns = ["crawl", "burrow", "lunge"]
            self.current_pattern = "crawl"
        elif kind == "spider":
            self.base_speed = 1.2
            self.movement_patterns = ["scuttle", "wall_climb", "pounce"]
            self.current_pattern = "scuttle"
            self.can_wall_climb = True
        elif kind == "slime":
            self.base_speed = 0.6
            self.movement_patterns = ["hop", "slide", "bounce"]
            self.current_pattern = "hop"
            self.hop_cooldown = 0
        elif kind == "ghost":
            self.base_speed = 0.9
            self.movement_patterns = ["drift", "chase", "phase"]
            self.current_pattern = "drift"
            self.phase_cooldown = 0
        
        # Enemy-specific attributes and special abilities
        if kind == "grub":
            self.max_health = 35
            self.health = self.max_health
            self.speed = 0.7
            self.damage = 12
            self.attack_range = 45
            self.behavior = "patrol"
            # Grub specific: can burrow and emerge
            self.burrow_cooldown = 0
            self.burrowed = False
            self.burrow_time = 0
            self.armor = 2  # Damage reduction
            self.poison_chance = 0.2  # Chance to apply poison on hit
            
        elif kind == "spider":
            self.max_health = 25
            self.health = self.max_health
            self.speed = 1.4
            self.damage = 15
            self.attack_range = 70
            self.behavior = "chase"
            self.jump_cooldown = 0
            # Spider specific: web mechanics
            self.web_cooldown = 0
            self.web_charges = 2
            self.web_recharge_time = 5.0
            self.crit_chance = 0.15  # Chance for double damage
            self.wall_cling = True  # Can move on walls
            
        elif kind == "slime":
            self.max_health = 45
            self.health = self.max_health
            self.speed = 0.5
            self.damage = 10
            self.attack_range = 35
            self.behavior = "bounce"
            self.jump_timer = 0
            # Slime specific: split and merge
            self.size = 2  # Can split into smaller sizes
            self.regeneration = 1  # Health regen per second
            self.split_threshold = 20  # Health at which it splits
            self.absorption = 0.2  # Damage reduction percentage
            
        elif kind == "ghost":
            self.max_health = 30
            self.health = self.max_health
            self.speed = 1.0
            self.damage = 14
            self.attack_range = 55
            self.behavior = "phase"
            self.phase_timer = 0
            self.visible = True
            # Ghost specific: phase abilities
            self.phase_duration = 2.0
            self.energy = 100  # Resource for special abilities
            self.energy_regen = 5  # Per second
            self.fear_radius = 80  # Area where player speed is reduced
            self.possession_cooldown = 0  # Can temporarily possess other enemies
        
        # Common enhancement systems
        self.level = 1
        self.exp_value = 10 * self.level
        self.status_effects = []
        self.special_cooldown = 0
        self.combo_counter = 0
        self.last_ability_time = time.time()

    def update(self, tiles, player_rect=None):
        now = time.time()
        dt = now - self.last_ability_time
        self.last_ability_time = now
        
        # Update status effects
        self.update_status_effects(dt)
        
        # Behavior patterns
        if player_rect:
            dx = player_rect.centerx - self.rect.centerx
            dy = player_rect.centery - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)
            
            if self.behavior == "patrol":
                # Grub: Advanced patrol with burrowing and intelligent movement
                if not self.burrowed:
                    patrol_range = 150
                    retreat_range = 60
                    
                    if dist < retreat_range:
                        # Too close - retreat and consider burrowing
                        self.vx = -math.copysign(self.speed * 1.2, dx)
                        if self.burrow_cooldown <= 0:
                            self.burrowed = True
                            self.burrow_time = now
                    elif dist < patrol_range:
                        # In range - approach cautiously
                        approach_speed = self.speed * (dist / patrol_range)  # Slower when closer
                        self.vx = math.copysign(approach_speed, dx)
                    else:
                        # Normal patrol - change direction occasionally
                        if random.random() < 0.02:
                            self.vx = random.choice([-1, 1]) * self.speed
                    
                    # Consider burrowing
                    if self.burrow_cooldown <= 0 and random.random() < 0.01:
                        self.burrowed = True
                        self.burrow_time = now
                        self.vx = 0
                else:
                    # While burrowed
                    if now - self.burrow_time > 2.0:
                        self.burrowed = False
                        self.burrow_cooldown = 5.0
                        # Emerge with an attack if player is nearby
                        if dist < 60:
                            self.attacking = True
                            self.attack_frame = 15
                
                if self.burrow_cooldown > 0:
                    self.burrow_cooldown -= dt
                
            elif self.behavior == "chase":
                # Spider: Advanced chase with web mechanics and tactical movement
                chase_range = 200
                optimal_range = 100  # Best distance for web attacks
                
                if dist < chase_range:
                    if self.wall_cling:
                        # Wall movement with better positioning
                        if dist < optimal_range:
                            # Back away while staying on walls
                            self.vx = -math.copysign(self.speed * 0.8, dx)
                            self.vy = math.copysign(self.speed * 0.6, dy)
                        else:
                            # Approach along walls
                            self.vx = math.copysign(self.speed, dx)
                            self.vy = math.copysign(self.speed * 0.7, dy)
                    else:
                        # Ground movement
                        if dist < optimal_range:
                            # Maintain distance for web attacks
                            self.vx = -math.copysign(self.speed * 0.5, dx)
                        else:
                            # Chase player
                            self.vx = math.copysign(self.speed * 1.2, dx)
                    
                    # Jump mechanics
                    if self.on_ground and self.jump_cooldown <= 0 and random.random() < 0.05:
                        self.vy = -8
                        self.jump_cooldown = 2.0
                        
                    # Web attack
                    if self.web_charges > 0 and self.web_cooldown <= 0 and random.random() < 0.02:
                        self.shoot_web(dx, dy)
                        self.web_charges -= 1
                        self.web_cooldown = 1.0
                
                # Update cooldowns
                if self.jump_cooldown > 0:
                    self.jump_cooldown -= dt
                if self.web_cooldown > 0:
                    self.web_cooldown -= dt
                
                # Recharge web
                if now - self.last_ability_time > self.web_recharge_time:
                    self.web_charges = min(2, self.web_charges + 1)
                    self.last_ability_time = now
                
            elif self.behavior == "bounce":
                # Slime: Advanced bounce with splitting and merging
                self.jump_timer += dt
                
                # Regeneration
                if self.health < 45:  # Max health
                    self.health = min(45, self.health + self.regeneration * dt)
                
                if self.on_ground and self.jump_timer >= 2.0:
                    # More aggressive jumping when closer
                    if dist < 200:
                        jump_power = -6 - (200 - dist) / 50  # Stronger jumps when closer
                        self.vx = math.copysign(self.speed * 1.5, dx)
                        self.vy = jump_power
                    else:
                        self.vx = random.choice([-1, 1]) * self.speed
                        self.vy = -4
                    self.jump_timer = 0
                    
                    # Create acid pool on landing
                    if random.random() < 0.3:
                        self.create_acid_pool()
                
                # Split mechanics
                if self.health <= self.split_threshold and self.size > 1:
                    self.split()
                
            elif self.behavior == "phase":
                # Ghost: Enhanced phase abilities
                self.phase_timer += dt
                self.energy = min(100, self.energy + self.energy_regen * dt)
                
                if self.phase_timer >= self.phase_duration:
                    self.visible = not self.visible
                    self.phase_timer = 0
                    
                    # Special phase-in attack
                    if self.visible and dist < 100 and self.energy >= 30:
                        self.phase_attack()
                        self.energy -= 30
                
                # Movement with energy consumption
                if dist < 180:
                    if self.visible or self.energy >= 10:
                        speed_mult = 1.5 if not self.visible else 1.0
                        self.vx = math.copysign(self.speed * speed_mult, dx)
                        self.vy = math.copysign(self.speed * speed_mult / 2, dy)
                        if not self.visible:
                            self.energy = max(0, self.energy - 10 * dt)
                            
                # Fear aura effect
                if dist < self.fear_radius:
                    self.apply_fear_effect()
            
            # Attack logic
            if dist <= self.attack_range and now - self.last_attack >= self.attack_cooldown:
                self.attacking = True
                self.last_attack = now
                self.attack_frame = 10  # Attack animation frames
                return True  # Signal that enemy is attacking
        
        # Enhanced movement and collision with unpredictable patterns
        if self.behavior != "phase":  # Ghost ignores normal physics
            # Add randomized motion
            if random.random() < 0.03:  # Small chance to change movement
                if self.kind == "spider":
                    # Spiders make sudden direction changes
                    self.vx = random.choice([-1.5, -1, 1, 1.5]) * self.speed
                    if random.random() < 0.3 and self.on_ground:  # Jump chance
                        self.vy = -7
                elif self.kind == "slime":
                    # Slimes bounce erratically
                    if self.on_ground and random.random() < 0.2:
                        self.vy = random.uniform(-8, -5)
                        self.vx = random.uniform(-1, 1) * self.speed
                elif self.kind == "grub":
                    # Grubs make small adjustments to speed
                    self.vx += random.uniform(-0.2, 0.2)
                    self.vx = max(-1.5, min(1.5, self.vx))  # Clamp speed
            
            # Apply sinusoidal vertical motion for flying/floating enemies
            if self.kind == "ghost":
                self.vy = math.sin(time.time() * 3) * 0.5
            
            # Horizontal movement with improved collision
            self.rect.x += int(self.vx)
            hit_wall = False
            for t in tiles:
                if self.rect.colliderect(t):
                    if self.vx > 0:
                        self.rect.right = t.left
                    else:
                        self.rect.left = t.right
                    hit_wall = True
            
            if hit_wall:
                if self.kind == "spider" and random.random() < 0.5:
                    # Spiders might climb walls
                    self.vy = -abs(self.vx)
                    self.vx *= -0.5
                else:
                    self.vx *= -1
            
            # Vertical movement with varied gravity
            if not self.on_ground:
                gravity = 0.4 if self.kind == "slime" else 0.6  # Slimes fall slower
                self.vy += gravity
            
            max_fall = 8 if self.kind == "spider" else 12  # Spiders fall slower
            self.vy = min(self.vy, max_fall)
            
            self.rect.y += int(self.vy)
            self.on_ground = False
            for t in tiles:
                if self.rect.colliderect(t):
                    if self.vy > 0:
                        self.rect.bottom = t.top
                        self.on_ground = True
                        self.vy = 0
                        if self.kind == "slime" and abs(self.vx) > 0.5:
                            # Slimes maintain momentum on landing
                            self.vy = -abs(self.vx) * 3
                    else:
                        self.rect.top = t.bottom
                        self.vy = 0
                        if self.kind == "spider":
                            # Spiders can stick to ceilings
                            self.on_ground = True
        else:
            # Ghost movement
            self.rect.x += int(self.vx)
            self.rect.y += int(self.vy)
        
        # Attack animation
        if self.attacking:
            self.attack_frame -= 1
            if self.attack_frame <= 0:
                self.attacking = False
        
        if self.health <= 0:
            self.dead = True
            
        return False  # No attack this frame

    def take_damage(self, damage):
        now = time.time()
        if now - self.last_hurt < 0.15:
            return
        self.last_hurt = now
        self.health -= damage
        
        # Add hit effect particle
        hit_particles = []
        for _ in range(5):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            hit_particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 0.5,
                'color': (255, 200, 200)
            })
        if not hasattr(self, 'hit_particles'):
            self.hit_particles = []
        self.hit_particles.extend(hit_particles)

    def draw(self, surf, camera_x):
        # Calculate position with camera offset
        draw_pos = (self.rect.x - camera_x, self.rect.y)
        
        # Get base image
        base_image = self.image.copy()
        
        # Add visual effects based on state
        if self.behavior == "phase":
            # Ghost phase effect
            if not self.visible:
                base_image.set_alpha(128)
            else:
                # Subtle pulse when visible
                pulse = (math.sin(time.time() * 5) + 1) / 2  # 0 to 1
                base_image.set_alpha(200 + int(55 * pulse))

        # Attack telegraph and execution effects
        now = time.time()
        if now - self.last_attack < self.attack_cooldown * 0.8:  # About to attack
            # Draw warning indicator
            if not self.attacking:  # Telegraph phase
                telegraph_progress = (now - self.last_attack) / (self.attack_cooldown * 0.8)
                # Enemy-specific warning effects
                if self.kind == "grub":
                    # Red mandible glow
                    warning_surf = pygame.Surface((8, 8))
                    warning_surf.fill((255, 0, 0))
                    warning_surf.set_alpha(int(200 * (math.sin(now * 15) + 1) / 2))
                    surf.blit(warning_surf, (draw_pos[0] + 8, draw_pos[1] + 8))
                
                elif self.kind == "spider":
                    # Pulsing web strands
                    for i in range(4):
                        angle = i * math.pi / 2 + now * 5
                        end_x = draw_pos[0] + math.cos(angle) * 15
                        end_y = draw_pos[1] + math.sin(angle) * 15
                        pygame.draw.line(surf, (255, 255, 255, 100),
                                      (draw_pos[0] + 8, draw_pos[1] + 8),
                                      (end_x + 8, end_y + 8), 2)
                
                elif self.kind == "slime":
                    # Bubbling effect
                    for _ in range(3):
                        bubble_x = draw_pos[0] + random.randint(2, 14)
                        bubble_y = draw_pos[1] + random.randint(2, 14)
                        size = random.randint(2, 4)
                        pygame.draw.circle(surf, (0, 255, 255, 150),
                                        (bubble_x, bubble_y), size)
                
                elif self.kind == "ghost":
                    # Expanding spectral ring
                    ring_radius = int(20 * telegraph_progress)
                    pygame.draw.circle(surf, (200, 200, 255, 100),
                                    (draw_pos[0] + 8, draw_pos[1] + 8),
                                    ring_radius, 2)
        
        if self.attacking:
            # Attack flash and effects
            attack_progress = min(1.0, self.attack_frame / 10.0)
            
            # Enemy-specific attack effects
            if self.kind == "grub":
                # Biting animation
                bite_offset = int(4 * attack_progress)
                flash_surf = base_image.copy()
                flash_surf.fill((255, 100, 100))
                flash_surf.set_alpha(int(200 * attack_progress))
                surf.blit(flash_surf, (draw_pos[0] + bite_offset, draw_pos[1]))
                
            elif self.kind == "spider":
                # Web shot effect
                web_length = int(30 * attack_progress)
                pygame.draw.line(surf, (255, 255, 255),
                               (draw_pos[0] + 8, draw_pos[1] + 8),
                               (draw_pos[0] + 8 + web_length, draw_pos[1] + 8), 3)
                
            elif self.kind == "slime":
                # Acid splash
                splash_radius = int(20 * attack_progress)
                pygame.draw.circle(surf, (100, 255, 100, 100),
                                (draw_pos[0] + 8, draw_pos[1] + 8),
                                splash_radius)
                
            elif self.kind == "ghost":
                # Spectral burst
                burst_size = int(40 * attack_progress)
                ghost_surf = pygame.Surface((burst_size, burst_size), pygame.SRCALPHA)
                pygame.draw.circle(ghost_surf, (200, 200, 255, int(100 * (1 - attack_progress))),
                                (burst_size//2, burst_size//2), burst_size//2)
                surf.blit(ghost_surf, (draw_pos[0] - burst_size//4, draw_pos[1] - burst_size//4))

            # Flash the enemy during attack
            flash_surf = base_image.copy()
            flash_surf.fill((255, 200, 200))
            flash_surf.set_alpha(int(100 * attack_progress))
            surf.blit(flash_surf, draw_pos)
        
        # Draw damage highlight
        now = time.time()
        if now - self.last_hurt < 0.3:  # Damage flash duration
            # White flash that fades out
            flash_alpha = int(255 * (1 - (now - self.last_hurt) / 0.3))
            flash_surf = base_image.copy()
            flash_surf.fill((255, 255, 255))
            flash_surf.set_alpha(flash_alpha)
            surf.blit(flash_surf, draw_pos)
            
            # Chromatic aberration effect
            if flash_alpha > 100:
                offset = int(2 * (flash_alpha / 255))
                # Red channel offset
                red_surf = base_image.copy()
                red_surf.fill((255, 0, 0))
                red_surf.set_alpha(flash_alpha // 3)
                surf.blit(red_surf, (draw_pos[0] + offset, draw_pos[1]))
                # Blue channel offset
                blue_surf = base_image.copy()
                blue_surf.fill((0, 0, 255))
                blue_surf.set_alpha(flash_alpha // 3)
                surf.blit(blue_surf, (draw_pos[0] - offset, draw_pos[1]))
        
        # Draw the base enemy
        surf.blit(base_image, draw_pos)
        
        # Update and draw hit particles
        if hasattr(self, 'hit_particles'):
            for particle in list(self.hit_particles):
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] -= 0.05
                if particle['life'] <= 0:
                    self.hit_particles.remove(particle)
                else:
                    alpha = int(255 * (particle['life'] / 0.5))
                    particle_surf = pygame.Surface((3, 3))
                    particle_surf.fill(particle['color'])
                    particle_surf.set_alpha(alpha)
                    particle_pos = (int(particle['x'] - camera_x), int(particle['y']))
                    surf.blit(particle_surf, particle_pos)
        
        # Draw health bar
        health_width = 24  # Width of health bar
        health_height = 3  # Height of health bar
        health_y_offset = -8  # Distance above enemy
        
        # Background (darker bar)
        bar_bg_rect = pygame.Rect(
            draw_pos[0] + (self.rect.width - health_width) // 2,
            draw_pos[1] + health_y_offset,
            health_width,
            health_height
        )
        pygame.draw.rect(surf, (60, 60, 60), bar_bg_rect)
        
        # Health percentage
        health_percent = self.health / self.max_health
        health_rect = pygame.Rect(
            draw_pos[0] + (self.rect.width - health_width) // 2,
            draw_pos[1] + health_y_offset,
            int(health_width * health_percent),
            health_height
        )
        
        # Color gradient based on health
        if health_percent > 0.7:
            health_color = (100, 255, 100)  # Green
        elif health_percent > 0.3:
            health_color = (255, 255, 100)  # Yellow
        else:
            # Pulsing red for low health
            pulse = (math.sin(now * 8) + 1) / 2
            red = int(200 + 55 * pulse)
            health_color = (red, 50, 50)
        
        pygame.draw.rect(surf, health_color, health_rect)
        
        # Border for health bar
        pygame.draw.rect(surf, (0, 0, 0), bar_bg_rect, 1)
        
        # Show movement direction indicator
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            move_angle = math.atan2(self.vy, self.vx)
            indicator_x = draw_pos[0] + 8 + math.cos(move_angle) * 12
            indicator_y = draw_pos[1] + 8 + math.sin(move_angle) * 12
            pygame.draw.circle(surf, (255, 255, 0), (int(indicator_x), int(indicator_y)), 2)
                
    def update_status_effects(self, dt):
        """Update temporary status effects"""
        for effect in list(self.status_effects):
            effect['duration'] -= dt
            if effect['duration'] <= 0:
                self.status_effects.remove(effect)

    def shoot_web(self, dx, dy):
        """Spider's web attack"""
        # Web projectile creation handled by game state
        self.attacking = True
        self.attack_frame = 8
        # Direction normalized
        total = abs(dx) + abs(dy)
        if total > 0:
            self.web_direction = (dx/total, dy/total)

    def create_acid_pool(self):
        """Slime creates damaging acid pool on ground"""
        self.status_effects.append({
            'type': 'acid_pool',
            'duration': 3.0,
            'damage': self.damage * 0.5,
            'rect': pygame.Rect(self.rect.x - 20, self.rect.y + self.rect.height - 5, 40, 5)
        })

    def split(self):
        """Slime splits into two smaller slimes"""
        self.size -= 1
        self.rect.width = int(self.rect.width * 0.7)
        self.rect.height = int(self.rect.height * 0.7)
        self.health = 25
        self.damage *= 0.7
        self.speed *= 1.2
        # New slime creation handled by game state

    def phase_attack(self):
        """Ghost's special phase-in attack"""
        self.attacking = True
        self.attack_frame = 15
        # Create circular attack area
        self.status_effects.append({
            'type': 'phase_burst',
            'duration': 0.5,
            'damage': self.damage * 1.5,
            'radius': 40
        })

    def apply_fear_effect(self):
        """Ghost's fear aura effect"""
        # Effect handled by game state - slows player in radius

    def get_hitbox(self):
        """Get the enemy's actual collision hitbox based on their type"""
        if self.kind == "spider":
            # Spider has a more compact hitbox due to legs
            return pygame.Rect(
                self.rect.x + 6,
                self.rect.y + 4,
                self.rect.width - 12,
                self.rect.height - 6
            )
        elif self.kind == "slime":
            # Slime has a wider but shorter hitbox
            return pygame.Rect(
                self.rect.x + 2,
                self.rect.y + self.rect.height//2,
                self.rect.width - 4,
                self.rect.height//2
            )
        elif self.kind == "ghost":
            # Ghost has a floating hitbox
            return pygame.Rect(
                self.rect.x + 4,
                self.rect.y + 2,
                self.rect.width - 8,
                self.rect.height - 6
            )
        else:  # grub
            # Grub has a longer hitbox
            return pygame.Rect(
                self.rect.x + 4,
                self.rect.y + 4,
                self.rect.width - 6,
                self.rect.height - 8
            )

    def get_attack_rect(self):
        """Get attack hitbox with enhanced effects per enemy type"""
        if self.attacking:
            # Use attack frame progress for growing/shrinking hitboxes
            progress = self.attack_frame / 10.0
            
            if self.kind == "grub":
                if self.burrowed:
                    # Emerge attack is larger and grows from center
                    size = int(30 * progress)
                    return pygame.Rect(
                        self.rect.centerx - size,
                        self.rect.centery - size,
                        size * 2,
                        size * 2
                    )
                else:
                    # Normal bite attack
                    width = int(20 * progress)
                    return pygame.Rect(
                        self.rect.centerx - width//2,
                        self.rect.y,
                        width,
                        self.rect.height
                    )
                    
            elif self.kind == "spider":
                # Spider attack grows outward
                size = int(40 * progress)
                rect = pygame.Rect(
                    self.rect.centerx - size//2,
                    self.rect.centery - size//2,
                    size,
                    size
                )
                if random.random() < self.crit_chance:
                    self.combo_counter += 1
                return rect
                
            elif self.kind == "slime":
                # Slime attack stays low to the ground
                width = int(50 * progress)
                rect = pygame.Rect(
                    self.rect.centerx - width//2,
                    self.rect.bottom - 10,
                    width,
                    12
                )
                if progress > 0.5:  # Create acid pool in later half of attack
                    self.create_acid_pool()
                return rect
                
            elif self.kind == "ghost":
                # Ghost attack can be either normal or phase burst
                for effect in self.status_effects:
                    if effect['type'] == 'phase_burst':
                        burst_size = int(effect['radius'] * 2 * progress)
                        return pygame.Rect(
                            self.rect.centerx - burst_size//2,
                            self.rect.centery - burst_size//2,
                            burst_size,
                            burst_size
                        )
                
                # Normal ghost attack is wide but not tall
                width = int(60 * progress)
                return pygame.Rect(
                    self.rect.centerx - width//2,
                    self.rect.centery - 8,
                    width,
                    16
                )
        return None
