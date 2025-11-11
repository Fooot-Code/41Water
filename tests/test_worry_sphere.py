import unittest
import time
from unittest.mock import Mock, MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from worry_sphere import WorrySphere


class TestWorrySphere(unittest.TestCase):
    
    def setUp(self):
        self.x = 100
        self.y = 200
        self.sphere = WorrySphere(self.x, self.y)
    
    def test_initialization_default_values(self):
        self.assertEqual(self.sphere.x, 100)
        self.assertEqual(self.sphere.y, 200)
        self.assertEqual(self.sphere.max_radius, 80)
        self.assertEqual(self.sphere.lifetime, 1.2)
        self.assertEqual(self.sphere.damage, 30)
        self.assertEqual(self.sphere.tick, 0.25)
        self.assertFalse(self.sphere.dead)
        self.assertEqual(self.sphere.last_tick, {})
    
    def test_initialization_custom_values(self):
        sphere = WorrySphere(50, 75, max_radius=100, lifetime=2.0, damage=50, tick=0.5)
        self.assertEqual(sphere.x, 50)
        self.assertEqual(sphere.y, 75)
        self.assertEqual(sphere.max_radius, 100)
        self.assertEqual(sphere.lifetime, 2.0)
        self.assertEqual(sphere.damage, 50)
        self.assertEqual(sphere.tick, 0.5)
    
    def test_age_calculation(self):
        time.sleep(0.1)
        age = self.sphere.age()
        self.assertGreaterEqual(age, 0.1)
        self.assertLess(age, 0.2)
    
    def test_progress_at_start(self):
        progress = self.sphere.progress()
        self.assertGreaterEqual(progress, 0.0)
        self.assertLessEqual(progress, 1.0)
    
    def test_progress_at_end(self):
        time.sleep(1.3)
        progress = self.sphere.progress()
        self.assertEqual(progress, 1.0)
    
    def test_progress_midway(self):
        time.sleep(0.6)
        progress = self.sphere.progress()
        self.assertGreater(progress, 0.4)
        self.assertLess(progress, 0.6)
    
    def test_radius_at_start(self):
        radius = self.sphere.radius()
        self.assertGreaterEqual(radius, 0)
        self.assertLess(radius, 10)
    
    def test_radius_increases_over_time(self):
        initial_radius = self.sphere.radius()
        time.sleep(0.3)
        later_radius = self.sphere.radius()
        self.assertGreater(later_radius, initial_radius)
    
    def test_radius_reaches_max(self):
        time.sleep(1.3)
        radius = self.sphere.radius()
        self.assertEqual(radius, self.sphere.max_radius)
    
    def test_update_expires_after_lifetime(self):
        enemies = []
        time.sleep(1.3)
        self.sphere.update(enemies)
        self.assertTrue(self.sphere.dead)
    
    def test_update_not_expired_before_lifetime(self):
        enemies = []
        self.sphere.update(enemies)
        self.assertFalse(self.sphere.dead)
    
    def test_update_damages_enemy_in_range(self):
        enemy = Mock()
        enemy.rect = Mock()
        enemy.rect.centerx = 100
        enemy.rect.centery = 200
        enemy.take_damage = Mock()
        
        time.sleep(0.5)
        self.sphere.update([enemy])
        
        enemy.take_damage.assert_called_once_with(30)
    
    def test_update_does_not_damage_enemy_out_of_range(self):
        enemy = Mock()
        enemy.rect = Mock()
        enemy.rect.centerx = 500
        enemy.rect.centery = 500
        enemy.take_damage = Mock()
        
        time.sleep(0.5)
        self.sphere.update([enemy])
        
        enemy.take_damage.assert_not_called()
    
    def test_update_respects_tick_cooldown(self):
        enemy = Mock()
        enemy.rect = Mock()
        enemy.rect.centerx = 100
        enemy.rect.centery = 200
        enemy.take_damage = Mock()
        
        time.sleep(0.3)
        self.sphere.update([enemy])
        self.assertEqual(enemy.take_damage.call_count, 1)
        
        self.sphere.update([enemy])
        self.assertEqual(enemy.take_damage.call_count, 1)
        
        time.sleep(0.3)
        self.sphere.update([enemy])
        self.assertEqual(enemy.take_damage.call_count, 2)
    
    def test_update_damages_multiple_enemies(self):
        enemy1 = Mock()
        enemy1.rect = Mock()
        enemy1.rect.centerx = 100
        enemy1.rect.centery = 200
        enemy1.take_damage = Mock()
        
        enemy2 = Mock()
        enemy2.rect = Mock()
        enemy2.rect.centerx = 110
        enemy2.rect.centery = 210
        enemy2.take_damage = Mock()
        
        time.sleep(0.5)
        self.sphere.update([enemy1, enemy2])
        
        enemy1.take_damage.assert_called_once_with(30)
        enemy2.take_damage.assert_called_once_with(30)
    
    def test_update_zero_radius_does_not_damage(self):
        enemy = Mock()
        enemy.rect = Mock()
        enemy.rect.centerx = 100
        enemy.rect.centery = 200
        enemy.take_damage = Mock()
        
        self.sphere.update([enemy])
        
        enemy.take_damage.assert_not_called()


if __name__ == '__main__':
    unittest.main()
