# main.py
import pygame, sys, time
from settings import *
from game_states import GameStateManager
from ui import draw_hud
from pygame.locals import *
import os

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    # create a low-resolution surface then scale up for pixel effect
    virtual = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

    gsm = GameStateManager(virtual)

    # start menu: choose class
    char_class = class_select(screen, virtual)
    gsm.start_new(char_class)

    running = True
    show_end = False
    guide_dialog_on = True
    last_attack_pressed = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        # input handling
        keys = pygame.key.get_pressed()
        inputs = {
            "left": keys[K_LEFT] or keys[K_a],
            "right": keys[K_RIGHT] or keys[K_d],
            "jump": (keys[K_UP] or keys[K_w] or keys[K_SPACE]),
            "dash": keys[K_k],
            "attack": keys[K_j]
        }
        for e in pygame.event.get():
            if e.type == QUIT:
                running = False
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    running = False
                if e.key == K_RETURN:
                    # advance dialog or stage
                    if gsm.stage_index == 2 and not show_end and gsm.boss and gsm.boss.health <= 0:
                        # defeated boss, end game
                        done = gsm.advance_stage_or_end()
                        show_end = done
            # handle clicks etc if needed

        # update game
        gsm.update(dt, inputs)

        # attacks
        # handle attack press (only when pressed, not held)
        if inputs["attack"] and not last_attack_pressed:
            did = gsm.player_attack_check()
            if did:
                # if you attack the guide (we don't have direct guide sprite), but we can simulate:
                # if there are few enemies and you still attack rapidly, reduce guide trust
                if len(gsm.enemies) == 0:
                    gsm.player.choice_points -= 1
        last_attack_pressed = inputs["attack"]

        # dash collisions
        gsm.dash_collision_check()

        # simple rule: if all enemies cleared in this stage, player can progress (via ENTER)
        # win check for boss
        if gsm.boss and gsm.boss.health <= 0:
            # show guide betrayal: set guide text and allow Enter to finish
            gsm.guide_text = "I guided you... but I needed 41 Water more than you."
            # reveal ending when ENTER pressed handled above

        # draw to virtual surface
        gsm.draw(virtual)

        # scale virtual to screen
        scaled = pygame.transform.scale(virtual, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(scaled, (0,0))
        pygame.display.flip()

        if gsm.ending:
            # show ending screen
            show_ending(screen, virtual, gsm.ending)
            running = False

    pygame.quit()
    sys.exit()

def class_select(screen, virtual):
    """Simple text-based class selection screen"""
    font = pygame.font.SysFont("consolas", 20)
    options = ["Wizard", "Worrier", "Ranger"]
    sel = 0
    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    sel = (sel - 1) % len(options)
                if e.key == pygame.K_RIGHT:
                    sel = (sel + 1) % len(options)
                if e.key == pygame.K_RETURN:
                    return options[sel]
        # draw
        virtual.fill((20,20,30))
        title = font.render("Choose your class", True, (230,230,230))
        virtual.blit(title, (10,10))
        for i, opt in enumerate(options):
            col = (255,255,100) if i==sel else (180,180,180)
            virtual.blit(font.render(opt, True, col), (20 + i*140, 60))
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
                pygame.quit(); sys.exit()
        virtual.fill((10,10,20))
        virtual.blit(font.render("Ending:", True, (220,220,220)), (10,10))
        virtual.blit(font.render(text, True, (220,220,220)), (10,50))
        screen.blit(pygame.transform.scale(virtual, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
