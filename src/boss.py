import pygame
import random

class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 64)  # larger than normal enemies
        self.health = 200
        self.vx = 0
        self.vy = 0
        self.attack_timer = 0
        self.attack_cooldown = 1.5  # seconds between attacks
        self.dead = False
        self.color = (150, 50, 50)  # reddish color

    def update(self, tiles, player_rect):
        if self.dead:
            return

        # Simple AI: Move towards player with some randomness
        dx = player_rect.centerx - self.rect.centerx
        self.vx = 2 if dx > 0 else -2
        
        # Random jumps
        if random.random() < 0.02:  # 2% chance per update
            self.vy = -10

        # Apply gravity
        self.vy += 0.5
        
        # Move and handle collisions
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
            # Adjust position for camera
            draw_rect = self.rect.copy()
            draw_rect.x -= camera_x
            draw_rect.y += shake_y
            
            pygame.draw.rect(surface, self.color, draw_rect)
            
            # Draw health bar with camera offset
            health_rect = pygame.Rect(
                self.rect.x - camera_x, 
                self.rect.y - 10 + shake_y,
                self.rect.width * (self.health / 200), 
                5
            )
            pygame.draw.rect(surface, (255, 0, 0), health_rect)
