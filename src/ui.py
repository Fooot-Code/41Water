# ui.py
import pygame
from settings import WHITE, UI_BG, PIXEL_SCALE
pygame.font.init()
FONT = pygame.font.SysFont("consolas", 12)

def draw_hud(surf, player, stage, guide_text=None, lives=None):
    # Enhanced HUD at top-left with stat bar
    # background bar - made wider and taller for stats
    pygame.draw.rect(surf, UI_BG, (2, 2, 220, 100))
    
    # Title and Class
    class_text = FONT.render(f"{player.char_class} - Level {stage}", True, WHITE)
    surf.blit(class_text, (6, 6))
    # Lives display (if provided)
    if lives is not None:
        lives_text = FONT.render(f"Lives: {lives}", True, WHITE)
        surf.blit(lives_text, (140, 6))
    
    # Health with bar
    health_percent = player.health / max(1, player.max_health)
    pygame.draw.rect(surf, (60, 0, 0), (6, 22, 100, 8))  # health bar background
    pygame.draw.rect(surf, (200, 0, 0), (6, 22, int(100 * health_percent), 8))  # health bar
    hp_text = FONT.render(f"HP: {player.health}/{player.max_health}", True, WHITE)
    surf.blit(hp_text, (110, 20))
    
    # Stats
    y = 36
    stats = [
        f"Attack Speed: {1/player.attack_cooldown:.1f}/s",
        f"Magic Power: {player.magic_power}",
        f"Defense: {player.defense}",
        f"Speed: {player.speed}",
        f"Special: {player.special_ability}"
    ]
    
    for stat in stats:
        text = FONT.render(stat, True, WHITE)
        surf.blit(text, (6, y))
        y += 12
    # guide dialog
    if guide_text:
        # draw box bottom
        box_h = 48
        w = surf.get_width()
        pygame.draw.rect(surf, UI_BG, (2, surf.get_height() - box_h - 2, w - 4, box_h))
        surf.blit(FONT.render(guide_text, True, WHITE), (6, surf.get_height() - box_h + 6))
