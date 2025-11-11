import unittest
from unittest.mock import Mock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pygame
pygame.init()

from boss import Boss


class TestBoss(unittest.TestCase):
    
    def setUp(self):
        self.boss = Boss(100, 200)
    
    def test_initialization(self):
        self.assertEqual(self.boss.rect.x, 100)
        self.assertEqual(self.boss.rect.y, 200)
        self.assertEqual(self.boss.rect.width, 64)
        self.assertEqual(self.boss.rect.height, 64)
        self.assertEqual(self.boss.health, 200)
        self.assertEqual(self.boss.vx, 0)
        self.assertEqual(self.boss.vy, 0)
        self.assertEqual(self.boss.attack_timer, 0)
        self.assertEqual(self.boss.attack_cooldown, 1.5)
        self.assertFalse(self.boss.dead)
        self.assertEqual(self.boss.color, (150, 50, 50))
    
    def test_take_damage_reduces_health(self):
        initial_health = self.boss.health
        self.boss.take_damage(50)
        self.assertEqual(self.boss.health, initial_health - 50)
        self.assertFalse(self.boss.dead)
    
    def test_take_damage_kills_boss(self):
        self.boss.take_damage(200)
        self.assertEqual(self.boss.health, 0)
        self.assertTrue(self.boss.dead)
    
    def test_take_damage_overkill(self):
        self.boss.take_damage(250)
        self.assertEqual(self.boss.health, -50)
        self.assertTrue(self.boss.dead)
    
    def test_update_moves_towards_player_right(self):
        tiles = []
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        initial_x = self.boss.rect.x
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.vx, 2)
    
    def test_update_moves_towards_player_left(self):
        tiles = []
        player_rect = pygame.Rect(50, 200, 20, 20)
        
        initial_x = self.boss.rect.x
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.vx, -2)
    
    def test_update_applies_gravity(self):
        tiles = []
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        initial_vy = self.boss.vy
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.vy, initial_vy + 0.5)
    
    def test_update_horizontal_collision_right(self):
        tile = pygame.Rect(150, 200, 32, 32)
        tiles = [tile]
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.rect.right, tile.left)
        self.assertEqual(self.boss.vx, 0)
    
    def test_update_horizontal_collision_left(self):
        tile = pygame.Rect(50, 200, 32, 32)
        tiles = [tile]
        player_rect = pygame.Rect(10, 200, 20, 20)
        
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.rect.left, tile.right)
        self.assertEqual(self.boss.vx, 0)
    
    def test_update_vertical_collision_bottom(self):
        tile = pygame.Rect(100, 270, 64, 32)
        tiles = [tile]
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        self.boss.vy = 10
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.rect.bottom, tile.top)
        self.assertEqual(self.boss.vy, 0)
    
    def test_update_vertical_collision_top(self):
        tile = pygame.Rect(100, 150, 64, 32)
        tiles = [tile]
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        self.boss.vy = -10
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.rect.top, tile.bottom)
        self.assertEqual(self.boss.vy, 1)
    
    def test_update_does_nothing_when_dead(self):
        self.boss.dead = True
        tiles = []
        player_rect = pygame.Rect(300, 200, 20, 20)
        
        initial_x = self.boss.rect.x
        initial_y = self.boss.rect.y
        
        self.boss.update(tiles, player_rect)
        
        self.assertEqual(self.boss.rect.x, initial_x)
        self.assertEqual(self.boss.rect.y, initial_y)


if __name__ == '__main__':
    unittest.main()
