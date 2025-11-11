import time
import pygame
import math
from player import Player


class Warrior(Player):
    """A heavier melee-focused subclass of Player.

    Warrior uses a short-range sword melee attack. We override attack and
    hitbox generation, and add a simple sword drawing while attacking.
    """
    def __init__(self, x, y):
        super().__init__(x, y, char_class="Warrior")
        # Tune warrior-specific stats
        self.max_health = 140
        self.health = 140
        self.attack_cooldown = 0.5
        self.defense = 50
        self.magic_power = 5
        self.speed = 1.6
        self.special_ability = "Shield Bash"
        # sword timing
        self.sword_frames = 14
        self.attack_range = 48

    def attack(self):
        now = time.time()
        if now - self.last_attack >= self.attack_cooldown:
            self.last_attack = now
            self.attacking = True
            self.attack_frame = self.sword_frames
            # sword is short but heavy
            self.attack_range = 48
            return True
        return False

    def get_attack_hitbox(self):
        """Return a rectangular melee hitbox in front of the warrior when attacking."""
        if not self.attacking or self.attack_frame <= 0:
            return None

        progress = self.attack_frame / float(max(1, self.sword_frames))
        # sword extends out then retracts; use (1-progress) to size the reach
        reach = int(self.attack_range * (1.0 - progress + 0.2))
        height = int(self.rect.height * 0.6)
        y = self.rect.centery - height // 2

        if self.facing > 0:
            x = self.rect.right
        else:
            x = self.rect.left - reach

        return pygame.Rect(x, y, max(1, reach), height)

    def draw(self, surface, camera_x=0):
        # reuse base drawing then draw sword when attacking
        super().draw(surface, camera_x)

        if self.attacking and self.attack_frame > 0:
            hb = self.get_attack_hitbox()
            if hb:
                draw_rect = hb.copy()
                draw_rect.x -= camera_x
                s = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                s.fill((220, 220, 200, 200))
                surface.blit(s, (draw_rect.x, draw_rect.y))

