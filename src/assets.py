# assets.py
# Procedural pixel art generator. All sprites are generated at runtime using pixel patterns
import pygame
from settings import PIXEL_SCALE, VIRTUAL_WIDTH, VIRTUAL_HEIGHT
import math

def make_surface(w, h):
    """Create a small 'pixel' surface (not scaled)."""
    # use SRCALPHA so we can scale cleanly
    return pygame.Surface((w, h), flags=pygame.SRCALPHA)

def scale_surface(surf):
    """Return a scaled surface according to PIXEL_SCALE."""
    size = (surf.get_width() * PIXEL_SCALE, surf.get_height() * PIXEL_SCALE)
    return pygame.transform.scale(surf, size)

def generate_player_sprite(char_class="Wizard"):
    """Return (idle_surf, attack_surf, dash_surf) scaled surfaces for player."""
    base_w, base_h = 12, 18
    idle = make_surface(base_w, base_h)
    attack = make_surface(base_w+6, base_h)
    dash = make_surface(base_w, base_h)
    # simple color palettes per class
    palettes = {
        "Wizard": ((60,40,120), (200,180,255)),
        "Worrier": ((120,50,40), (240,200,200)),
        "Ranger": ((40,100,50), (200,255,200))
    }
    main, accent = palettes.get(char_class, palettes["Wizard"])

    # idle: simple robe + face
    for x in range(base_w):
        for y in range(base_h):
            # face area
            if 4 <= x <= 7 and 2 <= y <= 5:
                idle.set_at((x,y), (220,200,160))
            # robe/body
            elif 3 <= x <= 8 and y >= 6:
                idle.set_at((x,y), main)
            # cloak/shadow
            elif 0 <= x <= base_w-1 and y >= base_h-3 and (x%2==0):
                # small pattern
                idle.set_at((x,y), (max(0,main[0]-10), max(0,main[1]-10), max(0,main[2]-10)))
    # accent on hood
    idle.set_at((5,2), accent)
    idle.set_at((6,2), accent)

    # Class-specific attack sprites
    aw = base_w + 8  # Wider for attack animations
    for x in range(aw):
        for y in range(base_h):
            if x < base_w:
                color = idle.get_at((x,y))
                if color.a != 0:
                    attack.set_at((x,y), color)
            else:
                # Weapon region
                weapon_x = x - base_w
                center = base_h // 2
                
                if char_class == "Wizard":
                    # Fireball effect
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
                        
                elif char_class == "Worrier":
                    # Sword slash effect (like Hollow Knight)
                    slash_height = max(1, int(6 * math.sin(weapon_x * math.pi / 4)))  # Ensure minimum height of 1
                    for offset in range(-slash_height, slash_height + 1):
                        y_pos = center + offset
                        if 0 <= y_pos < base_h:
                            # Main slash
                            alpha = int(255 * (1 - abs(offset) / slash_height))
                            attack.set_at((x, y_pos), (255, 255, 255, alpha))
                            # Trail effect
                            if weapon_x > 0:
                                trail_alpha = int(alpha * (1 - weapon_x/4))
                                if trail_alpha > 0:
                                    attack.set_at((x-1, y_pos), (200, 200, 255, trail_alpha))
                                    
                else:  # Ranger
                    # Arrow/energy projectile
                    if abs(y - center) <= 1:
                        # Arrow shaft
                        attack.set_at((x,y), accent)
                        # Glowing tip
                        if weapon_x >= 4:
                            glow = min(255, int(200 + 55 * math.sin(weapon_x * 0.8)))
                            attack.set_at((x,y), (glow, 255, glow, 200))
    # dash: slightly blurred duplicate (we'll draw a trailing pixel)
    for x in range(base_w):
        for y in range(base_h):
            color = idle.get_at((x,y))
            if color.a != 0:
                dash.set_at((x,y), color)
                if x < base_w-1:
                    # trail
                    dash.set_at((x+1,y), (min(255, color[0]+30), min(255,color[1]+30), min(255,color[2]+30)))

    return scale_surface(idle), scale_surface(attack), scale_surface(dash)

def generate_enemy_sprite(kind="grub"):
    """Detailed enemy pixel art surface with unique designs per type"""
    w, h = 16, 16
    s = make_surface(w, h)
    
    if kind == "grub":
        # Segmented worm-like creature
        body = (80, 200, 140)
        dark = (60, 150, 100)
        face = (30, 20, 10)
        
        # Draw segments
        for segment in range(3):
            center_x = w//2 - segment * 4
            center_y = h//2
            radius = 4 if segment == 0 else 3
            
            for x in range(w):
                for y in range(h):
                    dist = ((x-center_x)**2 + (y-center_y)**2)**0.5
                    if dist <= radius:
                        s.set_at((x,y), body)
                    elif dist <= radius + 1:
                        s.set_at((x,y), dark)
        
        # Eyes
        s.set_at((10,7), face)
        s.set_at((12,7), face)
        # Mandibles
        s.set_at((11,9), (120,50,50))
        s.set_at((13,9), (120,50,50))
        
    elif kind == "spider":
        # Detailed spider with legs
        body = (40, 40, 40)
        legs = (60, 60, 60)
        eye = (255, 0, 0)
        
        # Body segments
        for x in range(5, 11):
            for y in range(6, 10):
                s.set_at((x,y), body)
        for x in range(7, 9):
            for y in range(4, 6):
                s.set_at((x,y), body)
                
        # Eight legs
        leg_positions = [(4,6), (3,7), (4,8), (3,9),
                        (11,6), (12,7), (11,8), (12,9)]
        for pos in leg_positions:
            s.set_at(pos, legs)
            
        # Red eyes
        s.set_at((7,5), eye)
        s.set_at((8,5), eye)
        
    elif kind == "slime":
        # Translucent blob with inner core
        outer = (100, 200, 255, 128)
        inner = (50, 150, 255)
        shine = (200, 230, 255)
        
        # Blob shape
        for x in range(4, 12):
            height = int(4 * (1 - ((x-8)**2 / 16)))
            for y in range(8-height, 12):
                s.set_at((x,y), outer)
                
        # Core
        for x in range(6, 10):
            for y in range(8, 11):
                if (x-8)**2 + (y-9)**2 <= 4:
                    s.set_at((x,y), inner)
                    
        # Shine effects
        s.set_at((6,7), shine)
        s.set_at((7,7), shine)
        
    elif kind == "ghost":
        # Ethereal ghost with flowing form
        body = (200, 200, 255, 180)
        glow = (220, 220, 255, 128)
        core = (150, 150, 200)
        
        # Flowing form
        for x in range(4, 12):
            wave = int(math.sin(x * 0.8) * 2)
            for y in range(4+wave, 12+wave):
                if y < 8+wave:
                    s.set_at((x,y), glow)
                else:
                    s.set_at((x,y), body)
                    
        # Core/face
        for x in range(6, 10):
            for y in range(6, 9):
                s.set_at((x,y), core)
                
        # Eyes
        s.set_at((7,7), (0,0,0))
        s.set_at((8,7), (0,0,0))
    
    return scale_surface(s)

def generate_tile(tile_type="grass"):
    """Return a small tile surface (16x16) scaled up"""
    w,h = 16,16
    t = make_surface(w,h)
    if tile_type == "grass":
        # ground base
        for x in range(w):
            for y in range(h):
                if y >= 10:
                    t.set_at((x,y), (90,60,30))
                else:
                    t.set_at((x,y), (80,200,90) if (x+y)%3 else (60,180,70))
        # some pixels of texture
        for i in range(20):
            tx = (i*7) % w
            ty = 10 + (i*3)%6
            t.set_at((tx,ty), (50,40,25))
    elif tile_type == "rock":
        for x in range(w):
            for y in range(h):
                if (x+y)%2==0:
                    t.set_at((x,y),(120,120,140))
                else:
                    t.set_at((x,y),(100,100,120))
    else:
        for x in range(w):
            for y in range(h):
                t.set_at((x,y), (40,40,60))
    return scale_surface(t)
