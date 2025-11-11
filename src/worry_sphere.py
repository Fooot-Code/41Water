import pygame
import time

class WorrySphere:
    """Expanding AOE entity spawned by the Worrier class.

    It expands from the player's center up to max_radius over lifetime
    and damages enemies on contact with a cooldown per enemy.
    """
    def __init__(self, x, y, max_radius=80, lifetime=1.2, damage=30, tick=0.25):
        self.x = x
        self.y = y
        self.created = time.time()
        self.lifetime = lifetime
        self.max_radius = max_radius
        self.damage = damage
        self.tick = tick  # seconds between damage ticks per enemy
        self.last_tick = {}
        self.dead = False

    def age(self):
        return time.time() - self.created

    def progress(self):
        return min(1.0, max(0.0, self.age() / self.lifetime))

    def radius(self):
        return int(self.max_radius * self.progress())

    def update(self, enemies):
        # expire after lifetime
        if self.age() >= self.lifetime:
            self.dead = True
            return

        # damage enemies in range, respecting per-enemy tick cooldown
        r = self.radius()
        if r <= 0:
            return

        for e in enemies:
            # use enemy center
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
        # draw expanding translucent sphere
        r = self.radius()
        if r <= 0:
            return
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        alpha = int(200 * (1 - self.progress()))
        color = (255, 160, 180, alpha)
        pygame.draw.circle(s, color, (r, r), r)
        surf.blit(s, (self.x - r - camera_x, self.y - r + shake_y))
